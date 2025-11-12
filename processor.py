def analyze1(df , product_description):    
    import re
    import pandas as pd
    import nltk
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
    from nltk.stem import WordNetLemmatizer
    from collections import defaultdict
    from difflib import get_close_matches
    import numpy as np
    import math
    # print(df.head(1),product_description)

    # ---------- setup ----------
    # Download necessary NLTK resources quietly (without output)
    nltk.download('punkt', quiet=True)
    nltk.download('averaged_perceptron_tagger_eng', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('vader_lexicon', quiet=True)

    # Initialize sentiment analyzer and lemmatizer
    sia = SentimentIntensityAnalyzer()
    lem = WordNetLemmatizer()

    # ---------- generic words to exclude ----------
    # Common positive words
    generic_positive = {
        "good","great","nice","amazing","wonderful","excellent","fantastic","awesome",
        "brilliant","incredible","superb","outstanding","impressive","fabulous","perfect",
        "decent","pleasant","lovely","positive","splendid","terrific","cool"
    }
    # Common negative words
    generic_negative = {
        "bad","terrible","awful","poor","horrible","worst","disappointing","mediocre",
        "unpleasant","cheap","weak","flimsy","slow","boring","annoying","useless"
    }
    # Combined set to filter out from detailed pros/cons
    generic_words = generic_positive | generic_negative

    # ---------- contraction & cleaning ----------
    # Expand common English contractions
    def expand_contractions(text):
        text = re.sub(r"\bdoesn'?t\b", "does not", text)
        text = re.sub(r"\bdon'?t\b", "do not", text)
        text = re.sub(r"\bcan'?t\b", "can not", text)
        text = re.sub(r"\bwon'?t\b", "will not", text)
        text = re.sub(r"n\'t\b", " not", text)
        text = re.sub(r"\'re\b", " are", text)
        text = re.sub(r"\'s\b", " is", text)
        text = re.sub(r"\'ve\b", " have", text)
        return text

    # Clean text: lowercase, remove non-letter chars, collapse spaces
    def clean_text(s):
        if s is None: return ""
        s = expand_contractions(str(s).lower())
        s = re.sub(r'[^a-z\s]', ' ', s)
        s = re.sub(r'\s+', ' ', s).strip()
        return s

    # ---------- intensity calculation ----------
    def compute_intensity(row):
        text = row.get('review')
        rating = row.get('rating', 2.5)
        rating_dev = abs(rating - 2.5)  # deviation from neutral rating
        if not text:
            return (1 if rating > 2.5 else -1 if rating < 2.5 else 0) * rating_dev
        cleaned = clean_text(text)
        compound = sia.polarity_scores(cleaned)['compound']  # VADER compound score
        return compound * rating_dev  # weight by rating deviation

    df['intensity'] = df.apply(compute_intensity, axis=1)  # compute intensity per review

    # ---------- preprocess text ----------
    def keep_nouns_verbs(text):
        text = clean_text(text)
        tokens = nltk.word_tokenize(text)
        tokens = [t for t in tokens if t not in generic_words]  # remove generic words
        tagged = nltk.pos_tag(tokens)
        words = []
        for w, tag in tagged:
            if tag.startswith('NN'):  # nouns
                words.append(lem.lemmatize(w, 'n'))
            elif tag.startswith('VB'):  # verbs
                words.append(lem.lemmatize(w, 'v'))
        return " ".join(words)

    df['review'] = df['review'].apply(lambda t: keep_nouns_verbs(t if t else ""))  # preprocess reviews

    # ---------- aggregate features ----------
    def aggregate_features(df_subset):
        agg = defaultdict(float)
        for _, r in df_subset.iterrows():
            intensity = r['intensity']
            for t in nltk.word_tokenize(r['review']):
                if len(t) > 1:
                    agg[t] += intensity  # sum intensities per word
        return agg

    pros_df = df[df['intensity'] > 0]  # positive reviews
    cons_df = df[df['intensity'] < 0]  # negative reviews
    pros_agg = aggregate_features(pros_df)
    cons_agg = aggregate_features(cons_df)

    # ---------- merge near duplicates ----------
    def merge_similar_words(agg_dict, cutoff=0.85):
        merged = {}
        words = list(agg_dict.keys())
        for w in words:
            if any(w in group for group in merged.keys()):
                continue
            close = get_close_matches(w, words, n=5, cutoff=cutoff)  # similar words
            total = sum(agg_dict[c] for c in close)
            merged[w] = total
        return merged

    pros_agg = merge_similar_words(pros_agg)
    cons_agg = merge_similar_words(cons_agg)

    # ---------- resolve overlap ----------
    shared = set(pros_agg) & set(cons_agg)
    for word in list(shared):
        if abs(pros_agg[word]) >= abs(cons_agg[word]):
            del cons_agg[word]  # keep dominant sentiment
        else:
            del pros_agg[word]

    def top_k(agg, k=5):
        items = sorted([(w, s) for w, s in agg.items() if w.strip()], key=lambda x: -abs(x[1]))
        return items[:k]  # top k words by absolute intensity

    top_pros = top_k(pros_agg)
    top_cons = top_k(cons_agg)

    # ---------- relevance filtering (Option 2: word in product description) ----------
    def filter_relevant_words_fuzzy(phrases, product_description, cutoff=0.5):
        relevant = []
        desc_words = set(clean_text(product_description).split())
        for word, score in phrases:
            match = get_close_matches(word, desc_words, n=1, cutoff=cutoff)
            if match:
                relevant.append((word, score))
        return relevant

    top_pros = filter_relevant_words_fuzzy(top_pros, product_description)
    top_cons = filter_relevant_words_fuzzy(top_cons, product_description)

    #-----------legit words-----------------
    import nltk
    nltk.download('words', quiet=True)
    from nltk.corpus import words

    english_words = set(words.words())
    print(f"Total valid English words: {len(english_words)}")
    top_pros = [(w, s) for w, s in top_pros if w in english_words]
    top_cons = [(w, s) for w, s in top_cons if w in english_words]


    # ---------- scoring system ----------
    k = 25  # confidence saturation constant

    def confidence_weight(n_reviews, k=25):
        return (2 / math.pi) * math.atan(n_reviews / k)  # confidence as arctangent function

    def calc_summary_scores(pros, cons, n_reviews, k=25):
        pro_raw = sum(abs(i) for _, i in pros)
        con_raw = sum(abs(i) for _, i in cons)
        pro_score = pro_raw / n_reviews if n_reviews else 0
        con_score = con_raw / n_reviews if n_reviews else 0
        conf = confidence_weight(n_reviews, k)
        pro_score_adj = pro_score * conf
        con_score_adj = con_score * conf
        overall_score = (pro_score_adj - con_score_adj)
        return {
            "pro_score": round(pro_score_adj, 3),
            "con_score": round(con_score_adj, 3),
            "overall_score": round(overall_score, 3),
            "confidence": round(conf, 3),
            "reviews_used": n_reviews
        }

    scores = calc_summary_scores(top_pros, top_cons, len(df), k)
    pro_score = scores['pro_score']
    con_score = scores['con_score']
    overall_score = scores['overall_score']
    confidence = scores['confidence']

    # ---------- interpret summary ----------
    def interpret_summary_scores(pro_score, con_score, overall_score, confidence_score):
        # classify pro score
        if pro_score > 0.4:
            pro_label = "Excellent positive response"
        elif pro_score > 0.25:
            pro_label = "Strong positive feedback"
        elif pro_score > 0.1:
            pro_label = "Moderate positive feedback"
        else:
            pro_label = "Few or weak positives"

        # classify con score
        if con_score > 0.4:
            con_label = "Severe negative issues"
        elif con_score > 0.25:
            con_label = "Multiple recurring issues"
        elif con_score > 0.1:
            con_label = "Some mild concerns"
        else:
            con_label = "Few complaints"

        # classify overall score
        if overall_score >= 0.25:
            overall_label = "Excellent product"
        elif overall_score >= 0.10:
            overall_label = "Good product"
        elif overall_score >= 0.00:
            overall_label = "Average product"
        else:
            overall_label = "Poor product"

        # classify confidence
        if confidence_score >= 0.85:
            confidence_label = "Very High confidence (large & consistent review base)"
        elif confidence_score >= 0.70:
            confidence_label = "High confidence (good number of reviews)"
        elif confidence_score >= 0.50:
            confidence_label = "Moderate confidence (limited reviews)"
        else:
            confidence_label = "Low confidence (too few reviews)"

        summary = f"""
    ✅ Pro Score: {pro_score:.2f} → {pro_label}
    ❌ Con Score: {con_score:.2f} → {con_label}
    ⚖️ Overall Score: {overall_score:.2f} → {overall_label}
    📈 Confidence: {confidence_score:.2f} → {confidence_label}
    """
        return summary

    # ---------- OUTPUT ----------
    print("\nPros:")  # print top positive words
    for w, s in top_pros:
        print(f"✅ {w} ({s:.2f})")

    print("\nCons:")  # print top negative words
    for w, s in top_cons:
        print(f"❌ {w} ({s:.2f})")

    print("\n", interpret_summary_scores(pro_score, con_score, overall_score, confidence))  # print summary
    result={"pros":set(top_pros),"cons":set(top_cons),"summary":interpret_summary_scores(pro_score, con_score, overall_score, confidence)}
    return result
