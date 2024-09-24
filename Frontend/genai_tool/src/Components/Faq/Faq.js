import React, { useEffect, useState } from "react";
import Grid from "@mui/material/Grid";
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Container,
} from "@mui/material";
import "../Faq/Faq.css";
import promptIcon from "../../assets/images/promptIcon.png";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { api } from "../../services/api";
import axios from "axios";
import { useBackgroundColor } from "../../BackgroundContext";

const Faq = () => {
  const [faqJson, setFaqJson] = useState([]);
  const [apiUpdate, setApiUpdate] = useState(false);

  const { setNewBackgroundColor } = useBackgroundColor();
  setNewBackgroundColor("main-bg-linear");
  useEffect(() => {
    let url = `${process.env.REACT_APP_API_URL}faq`;
    const fetchData = async () => {
      try {
        const response = await api.get(url);
        const jsonData = response.data.data?.FAQs;
        setFaqJson(jsonData);
        setApiUpdate(true);
      } catch (error) {
        // Handle errors
        if (axios.isAxiosError(error)) {
          console.error("Axios Error:", error.message);
        } else {
          console.error("Error:", error.message);
        }
      }
    };
    fetchData();
  }, [apiUpdate]);

  return (
    <Container maxWidth="md">
      <Grid
        sm={12}
        className="promptContainer"
        container
        justifyContent={"center"}
      >
        <div style={{ marginBottom: "5px" }}>
          <h4 className="mt-0 text-center">
            Frequently Asked Questions (FAQs)
          </h4>
          {faqJson?.map((faqObj) => (
            <>
              <h5 className="text-blue m-0 faq-title">{faqObj.faq_string}</h5>
              {faqObj.type === "faq" &&
                faqObj.questions?.map((queObj) => (
                  <>
                    <Accordion
                      style={{
                        marginBottom: "10px",
                        borderRadius: "10px",
                      }}
                      className="fw-500"
                    >
                      <AccordionSummary
                        expandIcon={<ExpandMoreIcon className="f-primary" />}
                        aria-controls="panel1a-content"
                        id="panel1a-header"
                      >
                        <div className="question-style m-0">
                          {queObj.question}
                        </div>
                      </AccordionSummary>
                      <AccordionDetails>
                        <div
                          className="fw-500"
                          style={{ whiteSpaceCollapse: "preserve-breaks" }}
                        >
                          {queObj.answer}
                        </div>
                      </AccordionDetails>
                    </Accordion>
                  </>
                ))}
              {faqObj.type === "prompt" &&
                faqObj.questions.map((queObj) => (
                  <>
                    <Grid
                      sm={12}
                      className="faq-prompt d-block"
                      container
                      justifyContent="center"
                    >
                      <div className="faq-prompt-inner">
                        <img
                          width={"15px"}
                          src={promptIcon}
                          alt="Prompt Icon"
                          className="faq-prompt-img"
                        />
                        <span className="analyse-document-text">
                          "{queObj}"
                        </span>
                      </div>
                    </Grid>
                  </>
                ))}
            </>
          ))}
        </div>
      </Grid>
    </Container>
  );
};
export default Faq;
