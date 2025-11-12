'use client'
import React from "react"
import { useEffect, useRef, useState } from "react";
import { gsap } from 'gsap';
import { ScrollTrigger } from "gsap/ScrollTrigger";

// Register the plugin
gsap.registerPlugin(ScrollTrigger);
import axios from "axios";

function Page() {
  // landing animation

  useEffect(() => {
    let t = gsap.timeline()
    t.to("#logo h1", {
      opacity: 1,
      duration: 0.6,
      delay: 0.3,
      y: 20,
      stagger: 0.1
    })
    t.to("#logo", {
      delay: 0.8,
      opacity: 0,
      duration: 0.4
    })
    t.to("#logo", {
      zIndex: -1
    })
    t.to("#loading", {
      opacity: 0,
      duration: 0.2
    })
    t.to("#loading", {
      zIndex: -1
    })
    t.to("#cover div", {
      delay: -0.3,
      height: 0,
      duration: 0.5,
      stagger: 0.06,
      ease: "power3.out"
    })

    t.to("#cover", {
      zIndex: -1
    })

  }, []);
  const [stage, setStage] = useState("0%");
  const [link, setLink] = useState("");
  const [loading, setLoading] = useState(false);
  const Ref = useRef(null);
  const dRef = useRef(null);

  const [pros, setPros] = useState([]);
  const [cons, setCons] = useState([]);
  const [summary, setSummary] = useState("sdfsdfsfsfsd dsfsdfsdf sdfsdfsdf");
  // Animate stage from 0% -> 100% over 6 seconds
  useEffect(() => {
    gsap.to({ value: 0 }, {
      value: 100,
      duration: 3,
      onUpdate: function () {
        setStage(Math.round(this.targets()[0].value) + "%");
      }
    });
  }, []);

  
  // Handle form submission
  const handleSubmit = async (e) => {

    e.preventDefault();
    setLoading(true);

    //  GSAP loader animation placeholder
    // -------------------------------------
    // Example: gsap.to("#loader_space", { rotation: 360, repeat: -1 });
    // -------------------------------------
    gsap.to("#loader_space",{
      zIndex:2
    })

    try {
      console.log(link)
      const res = await axios.post("http://localhost:8000/analyze", {
        link: link,

      });

      console.log("Response from FastAPI:", res, res.data.result.pros, res.data.result.cons);
      // Set pros and cons to state

      // summary setup
      setSummary(res.data.result.summary);
      // we have to choose only 0th feature of every element
      const onlyConsStrings = res.data.result.cons.map(item => item[0]);

      // Remove duplicates using Set
      const uniqueCons = [...new Set(onlyConsStrings)];

      setCons(uniqueCons);

      const onlyConsStrings2 = res.data.result.pros.map(item => item[0]);
      const uniqueCons2 = [...new Set(onlyConsStrings2)];

      setPros(uniqueCons2);


    } catch (err) {
      console.error("Error fetching data:", err);
    } finally {
      setLoading(false);
      // 👇 Stop GSAP loader animation here
      // gsap.killTweensOf("#loader_space");
      gsap.to("#loader_space",{
        zIndex:-2
      })
      gsap.to("#output", {
        display: "flex"
      })
      let f = gsap.timeline()
      f.to("#down", {
        zIndex: 1
      })
      f.to("#down", {
        opacity: 1,
        duration: 1.7
      })
      f.to("#down", {
        left: "80px",
        scale: 2,
        duration: 4
      })
    }
  };

  // we will create a function here which will control the scroll effects of pros and cons(output in short)
  // scrollTrigger:{
  //         trigger:"#box1",
  //         scroller:"body",
  //         markers:true,

  //         start:"top 40%",
  //         end:"top 0%",

  //         // takes 1-5 value,value increases, smoothness increases
  //         scrub:2

  //       }
  if (Ref.current) {

    gsap.to("#output div", {
      opacity: 1,
      y: 10,
      scrollTrigger: {
        trigger: "#output",
        scroller: "body",
        // markers:true,

        start: "top 30%",
        end: "top 30%",
        scrub: 2
      }
    })
  }

  function change() {
    let t = gsap.timeline();
    t.to("#instructions_container", {
      opacity: 0,
      y: -10,
      duration: 0.4
    })
    t.to("#instructions_container", {
      zIndex: -1
    })
    t.to("#blurry", {
      delay: -0.3,
      opacity: 0,
      duration: 0.4
    })
    t.to("#blurry", {
      zIndex: -1,
      delay: -0.2
    })
  }
  return <>
    {/* landing animation divs */}
    <div id="logo">
      <h1>I</h1>
      <h1>N</h1>
      <h1>S</h1>
      <h1>I</h1>
      <h1>G</h1>
      <h1>H</h1>
      <h1>T</h1>
    </div>
    <div id="loading">{stage}</div>
    <div id="cover">
      <div></div>
      <div></div>
      <div></div>
      <div></div>
      <div></div>
    </div>


    <div id="instructions_container">
      <div id="instruct">
        <h1>HOW TO USE</h1>
        <p>Paste a product link, and Insight’s AI-powered engine instantly analyzes reviews to reveal clear pros, cons, and overall sentiment — helping you make smarter, faster buying decisions.</p>
        <div id="but"><button onClick={change}> Understood</button></div>

      </div>
    </div>
    <div id="blurry"></div>
    <div id="back">

      <video className="video" autoPlay loop muted playsInline>
        <source src="/red-lightning-background.mp4" type="video/mp4" />

      </video>

    </div>


    <div id="down">
      🔻
    </div>

    {/* main form content */}

    <h1 id="paste">ENTER PRODUCT LINK</h1>
    <form id="input_taker" onSubmit={handleSubmit}>
      <input placeholder="product link" value={link} onChange={(e) => { setLink(e.target.value) }}></input>
      <button type="submit">Analyze</button>
    </form>

    <div id="output" ref={Ref}>
      <div>
        <h1>PROS</h1>
        <ul>
          {pros.map((item, idx) => (
            <li key={idx}>{idx + 1} {item}</li>
          ))}
        </ul>
      </div>
      <div>
        <h1>CONS</h1>
        <ul>
          {cons.map((item, idx) => (
            <li key={idx}>{idx + 1} {item}</li>
          ))}
        </ul>
      </div>
      <div>
        <h1>SUMMARY EVALUATION</h1>
        <p>{summary}</p>
      </div>
    </div>

    {/* loading here */}
    <div id="loader_space">
      <div id="load">
        <div id="server"><h1>SERVER</h1></div>
        <div id="right1"></div>
        <div id="down1"></div>
        <div id="left"></div>
        <div id="down2"></div>
        <div id="right2"></div>
        <div id="system"><h1>SYSTEM</h1></div>
        <div id="display"></div>
        <div id="r1"></div>
        <div id="d1"></div>
        <div id="l1"></div>
        <div id="d2"></div>
        <div id="datadot" ref={dRef}></div>

      </div>
    </div>
  </>
}
export default Page