def do1(link):    
    import requests
    import pandas as pd

    # --- Configuration ---
    API_KEY = "...."

    def get_asin(url):
        parts = url.split("/")
        if "dp" in parts:
            return parts[parts.index("dp") + 1]
        elif "product" in parts:
            return parts[parts.index("product") + 1]
        else:
            return None

    ASIN = get_asin(link)
    COUNTRY = "IN"  # change to "US" if needed

    BASE_URL = "https://real-time-amazon-data.p.rapidapi.com"
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "real-time-amazon-data.p.rapidapi.com"
    }

    # --- 1️⃣ Fetch product details ---
    print("Fetching product details...")
    prod_url = f"{BASE_URL}/product-details"
    params = {"asin": ASIN, "country": COUNTRY}
    resp = requests.get(prod_url, headers=headers, params=params)

    if resp.status_code == 200:
        # extract the "data" part of the response
        prod_data = resp.json().get("data", {})

        product_title = prod_data.get("product_title", "N/A")

        # ✅ Correct line to get product_description
        product_description = prod_data.get("product_description", "")
        # print(type(product_description),type(prod_data))
        # If description is empty, try using "about_product"
        if not product_description:
            about_list = prod_data.get("about_product", [])
            if isinstance(about_list, list):
                product_description  = " ".join(about_list)

        print("✅ Product details fetched successfully!")
        print("\nTitle:", product_title)
        print("\nDescription:", product_description[:300], "..." if len(product_description) > 300 else "")
    else:
        print("⚠️ Failed to fetch product details:", resp.status_code, resp.text)
        product_title = "N/A"
        product_description = ""

    # --- 2️⃣ Fetch product reviews (multiple pages) ---
    print("\nFetching product reviews...")
    all_reviews = []

    for page in range(1, 6):  # Get up to 5 pages (~50 reviews)
        review_url = f"{BASE_URL}/product-reviews"
        params = {"asin": ASIN, "country": COUNTRY, "page": str(page)}
        r = requests.get(review_url, headers=headers, params=params)
        if r.status_code != 200:
            print(f"⚠️ Page {page} failed ({r.status_code})")
            continue
        data = r.json().get("data", {})
        reviews = data.get("reviews", data)
        if not isinstance(reviews, list) or len(reviews) == 0:
            print(f"⚠️ Page {page} returned no reviews.")
            break
        all_reviews.extend(reviews)
        print(f"✅ Page {page}: {len(reviews)} reviews fetched.")

    # --- 3️⃣ Create DataFrame ---
    if not all_reviews:
        print("⚠️ No reviews found for this product.")
        df = pd.DataFrame(columns=["review", "rating"])
    else:
        df = pd.DataFrame(all_reviews)
        keep_cols = [c for c in ["review_title", "review_comment", "review_star_rating"] if c in df.columns]
        df = df[keep_cols]
        df["review"] = df["review_title"].fillna("") + " " + df["review_comment"].fillna("")
        df["rating"] = df["review_star_rating"].astype(float)
        df = df[["review", "rating"]]

    print(f"\n✅ DataFrame 'df' created successfully with {len(df)} reviews!")
    # print(df.head())
    return df, product_description