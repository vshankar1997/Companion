import "../Landing/Landing.css";
import React, { useEffect, useState } from "react";
import Grid from "@mui/material/Grid";
import { Button } from "@mui/material";
import { useNavigate } from "react-router-dom";
import landing_QA_img from "../../assets/images/Answer_Questions.png";
import landing_upload_img from "../../assets/images/Analyze.png";
import landing_result_img from "../../assets/images/Export.png";
import Venn_Diagram from "../../assets/images/Process_Diagram.png";
import { useBackgroundColor } from "../../BackgroundContext";
const Landing = () => {
  const navigate = useNavigate();
  const { setNewBackgroundColor } = useBackgroundColor();
  const [curState, setCurState] = useState("page1");
  setNewBackgroundColor("main-bg");

  // array of objects to render images and text in landing page
  const imageUrls = [
    {
      img: landing_QA_img,
      title: "Answer Questions About Disease States and Treatments",
      description:
        "Use natural language to ask me questions or make requests, just like you’d talk to a coworker.",
    },
    {
      img: landing_upload_img,
      title: "Analyze Information You Upload",
      description:
        "Submit your notes, files, or published papers, and simply tell me how you’d like me to analyze them.",
    },
    {
      img: landing_result_img,
      title: "Export and Share Results",
      description:
        "Create new content such as document summaries from your queries to use as a first draft for sharing with others.",
    },
  ];

  useEffect(() => {
    setCurState("page1")
  }, [])

  const navigateToHome = () => {
    setCurState("page1");
    navigate("/prompt");
  }
  return (
    <Grid container spacing={2}>
      <Grid
        item
        xs={12}
        className="promptContainer"
        container
        direction="row"
        justifyContent="center"
        alignItems="center"
      >
        {curState === "page1" && <div>
          <Grid container justifyContent={"center"}>
            <h4 className="text-dark text-center mt-2 m-0">What Can I Do For You?</h4>
          </Grid>
          <Grid container>
            {imageUrls.map((imgObj) => (
              <Grid item xs={12} sm={6} md={4}>
                <div style={{ padding: 16, textAlign: "center" }}>
                  <img
                    src={imgObj.img}
                    style={{ maxWidth: "50%", height: "auto" }}
                    alt="image"
                  />
                  <h6 className="text-blue mt-2 mb-0 bold">{imgObj.title}</h6>
                  <p className="text-blue">{imgObj.description}</p>
                </div>
              </Grid>
            ))}
          </Grid>
        </div>}
        

        {curState === "page2" && <div><Grid container>
          <Grid item xs={12}>
            <div
              style={{ padding: 9, textAlign: "center" }}
              className="text-center"
            >
              <h4 className="text-dark text-center mt-2">{curState === "page1" ? 'What Can I Do For You?' :  'Where Does My Information Come From?'}</h4>
              <div style={{ position: "relative" }}>
                <img
                  src={Venn_Diagram}
                  style={{ width: "40%", height: "auto" }}
                  alt="image"
                />
              </div>
            </div>
          </Grid>
        </Grid></div>}

        <Grid container>
          <Grid item xs={12}>
            <div
              style={{ padding: 16, textAlign: "center" }}
              className="text-center"
            >
              {curState === "page2" && <Button
                size="large"
                style={{ textTransform: "math-auto" }}
                className="text-center"
                onClick={() => setCurState("page1")}
              >
                Back
              </Button>}
              <Button
                variant="contained"
                size="large"
                style={{ textTransform: "math-auto", marginLeft: "10px" }}
                className=" text-center"
                onClick={curState === "page1" ? () => setCurState("page2") : navigateToHome}
              >
                Next
              </Button>
            </div>
          </Grid>
        </Grid>
      </Grid>
    </Grid>
  );
};

export default Landing;
