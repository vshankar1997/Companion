import React, { useEffect, useRef, useState } from "react";
// import { parseAnswerToHtml } from "./AnswerParser";
import {
  Card,
  Grid,
  CardContent,
  Typography,
  Stack,
  styled,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Button,
  TextareaAutosize,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import RemoveIcon from '@mui/icons-material/Remove';
import AddIcon from '@mui/icons-material/Add';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import SentimentVeryDissatisfiedIcon from '@mui/icons-material/SentimentVeryDissatisfied';
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import SentimentNeutralIcon from '@mui/icons-material/SentimentNeutral';
import SentimentSatisfiedAltIcon from '@mui/icons-material/SentimentSatisfiedAlt';
import CloseIcon from '@mui/icons-material/Close';
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import Tooltip, { tooltipClasses } from "@mui/material/Tooltip";
import AutorenewIcon from "@mui/icons-material/Autorenew";
import { api } from "../../services/api";
import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import axios from "axios";
import ThumbUpOffAltIcon from '@mui/icons-material/ThumbUpOffAlt';
import ThumbUpAltIcon from '@mui/icons-material/ThumbUpAlt';
import ThumbDownOffAltIcon from '@mui/icons-material/ThumbDownOffAlt';
import ThumbDownAlt from "@mui/icons-material/ThumbDownAlt";
import * as marked from "marked";
import answerIcon from "../../assets/images/Avatar.png";
import OpenInFullIcon from '@mui/icons-material/OpenInFull';
import DynamicModal from "../Modal/DynamicModal";
import Carousel from "../Modal/Carousel";
// import BlinkingDots from "./BlinkingDots";
export const Answer = ({
  regenerate,
  answer,
  sources,
  msg_id,
  rating = "",
  isFeedback,
  updateState,
  makeApiRequest,
  makeApiRequestStreaming,
  type = "",
  feedback = {},
  image_details = {},
  get_only_images = false
}) => {
  // tooltip component
  const BootstrapTooltip = styled(({ className, ...props }) => (
    <Tooltip placement="top" {...props} arrow classes={{ popper: className }} />
  ))(({ theme }) => ({
    [`& .${tooltipClasses.arrow}`]: {
      color: theme.palette.common.black,
    },
    [`& .${tooltipClasses.tooltip}`]: {
      backgroundColor: theme.palette.common.black,
    },
  }));

  const [isCopy, setIsCopy] = useState(false);
  const htmlContentRef = useRef(null);
  const selectRef = useRef(null);
  const [sourceObj, setSourceObj] = useState(sources);
  const [isExpanded, setIsExpanded] = useState(false);
  const [imgExpanded, setImgExpanded] = useState(get_only_images);
  const [isSourceUpdate, setIsSourceUpdate] = useState(false);
  const [answerModify, setAnswerModify] = useState([]);
  const accordionRef = useRef(null);
  const [shouldScroll, setShouldScroll] = useState(false);
  const [target, setTarget] = useState("");
  const [showFeedbackForm, setShowFeedbackForm] = useState(false);
  const [isSubmit, setIsSubmit] = useState(true);
  const [feedbackMessage, setFeedbackMessage] = useState("");
  const [isFeedbackUpdate, setIsFeedbackUpdate] = useState(false);
  const [imageData, setImageData] = useState({});
  const [currentIndex, setCurrentIndex] = useState(0);

  let feedbackObj = {
    tag_ratings: (Object.keys(feedback).length === 0 || Object.keys(feedback.tag_ratings).length === 0) ? { accurate: 0, comprehensive: 0, relevant: 0 } : feedback.tag_ratings,
    feedback: feedback.feedback
  }
  const [feedbackForm, setFeedbackForm] = useState(feedbackObj);

  useEffect(() => {
    if (shouldScroll) {
      const element = document.getElementById(target);
      if (element) {
        element.scrollIntoView({ behavior: "smooth" });
        setShouldScroll(false); // Reset shouldScroll
      }
    }
  }, [shouldScroll]);

  useEffect(() => {
    if (Object.keys(feedback).length > 0) {
      setFeedbackForm(feedback);
    }
    const regex = /_@_[\w-]+\.pdf/g;
    const updatesMessage = answer.replace(regex, '.pdf');
    getTextData(updatesMessage);
  }, []);

  useEffect(() => {
    setFeedbackForm(feedbackForm);
  }, [isFeedbackUpdate]);

  const handleFeedbackTags = (like, category, value) => {
    let feedbackData = feedbackForm;
    if (like === "like") {
      if (value === 0 || value === -1) {
        feedbackData.tag_ratings[category] = 1;
      } else {
        feedbackData.tag_ratings[category] = 0;
      }
    } else {
      if (value === -1) {
        feedbackData.tag_ratings[category] = 0;
      } else {
        feedbackData.tag_ratings[category] = -1;
      }
    }
    setIsSubmit(false);
    setIsFeedbackUpdate(!isFeedbackUpdate);
    setFeedbackForm(feedbackData);
  }

  const setFeedbackMsg = (msg) => {
    let feedbackData = feedbackForm;
    feedbackData.feedback = msg;
    setIsSubmit(false);
    setIsFeedbackUpdate(!isFeedbackUpdate);
    setFeedbackForm(feedbackData);
  }

  const trimDocId = (docName) => {
    let docContent = docName.split("_@_")[docName.split("_@_").length - 1];
    docContent = docContent.split(".")[0];
    docContent = "_@_" + docContent;
    return docName.replace(docContent, "");
  };

  const getTextData = (text) => {
    window.setTimeout(() => {
      let regex = /\[\$\{(\d+)\}\]/g;
      if (sources.length > 0 && typeof (sources[0].content) === "object") {
        regex = /\[\$\{(\d+\w)\}\]/g
      }
      setSourceObj(prevData => {
        return prevData.map((subArray, index) => {
          subArray.isExpanded = false;
          return subArray;
        });
      });
      let chunkArr = text.split(regex);
      setAnswerModify(chunkArr);
    }, 300)
  };

  const handleCopyClick = async (answer, sources) => {
    const range = document.createRange();
    range.selectNode(htmlContentRef.current);
    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
    try {
      document.execCommand("copy");
      setIsCopy(true);
      window.setTimeout(() => {
        setIsCopy(false);
      }, 2000);
    } catch (error) {
      console.error("Unable to copy to clipboard:", error);
    }
    selection.removeAllRanges();
  };

  const handleChange = (event, expanded) => {
    setIsExpanded(expanded);
  };

  const handleImageAccordion = (event, expanded) => {
    setImgExpanded(!imgExpanded);
  };

  const handleSourceAccordion = (obj) => {
    setSourceObj(prevData => {
      return prevData.map((subArray, index) => {
        if (subArray.DocumentName === obj.DocumentName) {
          subArray.isExpanded = !subArray.isExpanded;
        }
        return subArray;
      });
    })
  };

  /*
  - Function to update the rating provided by the user
  - Author - Vinay K M
  - Updated by - Vinay K M
  */
  const setFeedback = async (val, type) => {
    let requestData = {};
    if (type === "rating") {
      requestData = {
        msg_id: msg_id,
        rating: val,
      };
    } else {
      requestData = {
        msg_id: msg_id,
        tag_ratings: feedbackForm.tag_ratings,
        feedback: feedbackForm.feedback,
      };
    }
    try {
      let url = `${process.env.REACT_APP_API_URL}feedback`;
      await api.put(url, requestData);
      if (type === "rating") {
        updateState(msg_id, val);
        setFeedbackMessage("");
      } else {
        setFeedbackMessage("Thank you for your feedback!");
      }
    } catch (error) {
      if (axios.isAxiosError(error)) {
        // Axios-specific error handling
        console.error("Axios Error:", error.message);
        console.error("Response Data:", error.response?.data);
      } else {
        // General error handling
        console.error("Error:", error.message);
      }
    }
  };

  const closeFeedback = () => {
    // send feedbadk here
    setShowFeedbackForm(false);
  }

  const handleLike = (like) => {
    setFeedback(like, "rating");
    setShowFeedbackForm(true);
  };

  const [isModalOpen, setModalOpen] = useState(false);

  // const handleOpenModal = () => {
  //   setModalOpen(true);
  // };

  const handleCloseModal = () => {
    setModalOpen(false);
  };

  /*
  - Function to render dymanic modal as per the param
  - Author - Vinay K M
  - Updated by - Vinay K M
  */
  const modalTitle =
    "Related Images";

  const showImageDetails = (data, index) => {
    setImageData(data);
    setModalOpen(true);
    setCurrentIndex(index)
  }

  const modalContent = (
    <>
      {Object.keys(imageData).length > 0 &&
        <>
          <Carousel images={image_details} currentIndex={currentIndex} setCurrentIndex={setCurrentIndex} msg_id={msg_id} />
        </>
      }
    </>
  );
  const modalActions = (<></>);

  const handleLink = (number, target) => {
    setIsExpanded(true);
    let digit = target.split("-")[1].match(/\d+/);
    if (digit) {
      setSourceObj(prevData => {
        return prevData.map((subArray, index) => {
          if (index === parseInt(digit[0], 10) - 1) {
            subArray.isExpanded = true;
            return subArray;
          } else {
            return subArray;
          }
        });
      });
    }
    setTimeout(() => {
      setIsSourceUpdate(!isSourceUpdate);
      setTarget(target);
      setShouldScroll(true);
    }, 1000);
  };

  useEffect(() => {
    window.setTimeout(() => {
      var links = document.getElementsByClassName("footnote-link");
      for (let i = 0; i < links.length; i++) {
        links[i].addEventListener("click", function (event) {
          event.preventDefault();
          handleLink(i, links[i].getAttribute("data-targetid"));
        }, false);
      }
    }, [1000])
  }, [])

  useEffect(() => {
    setSourceObj(sourceObj);
  }, [isSourceUpdate])

  const renderData = () => {
    let answerObj = "";
    answerModify.forEach((item, index) => {
      let integerValue = parseInt(item);
      if (!isNaN(integerValue) && Number.isInteger(integerValue)) {
        answerObj += `<a key=${index} class='footnote-link' href='#' data-targetId=${msg_id}c-${item}>[${item}]</a>`;
      } else {
        answerObj += item;
      }
    });
    answerObj = marked.parse(answerObj);
    return (
      <Typography
        variant="body2"
        sx={{ margin: "0em", whiteSpace: "pre-line" }}
        dangerouslySetInnerHTML={{ __html: answerObj }}
      />
    );
  };

  return (
    <Stack
      direction="row"
      spacing={1}
      className="animate__animated animate__fadeInUp answer-wrapper"
    >
      <div>
        <img src={answerIcon} alt="answer icon" width="32px" height="32px" />
      </div>
      <Card
        variant="elevation"
        style={{ background: "transparent", boxShadow: "none" }}
      >
        <CardContent
          sx={{
            pb: (theme) => `${theme.spacing(2)} !important`,
            // background: "rgb(249, 249, 249)",
            borderRadius: 2,
            boxShadow: "0px 2px 1px -1px rgba(0,0,0,0.2), 0px 1px 1px 0px rgba(0,0,0,0.14), 0px 1px 3px 0px rgba(0,0,0,0.12)"
          }}
          id="copyableCard"
          className="copyableCard answer-border"
          ref={htmlContentRef}
        >
          <span>{renderData()}</span>
        </CardContent>
        <Grid className="d-flex">
          {
            <Button
              className="btn-copy"
              id={regenerate ? "last-source" : "last-source-1"}
              onClick={() => handleCopyClick(answer, sources)}
            >
              <BootstrapTooltip
                title={
                  <React.Fragment>
                    {!isCopy && (
                      <span color="inherit">Copy to clipboard</span>
                    )}
                    {isCopy && <span color="inherit">Copied</span>}
                  </React.Fragment>
                }
              >
                <span>
                  {!isCopy && <ContentCopyIcon className="font-14" />}
                  {isCopy && <CheckCircleOutlineIcon className="font-14" />}
                  &nbsp;Copy
                </span>
              </BootstrapTooltip>
            </Button>
          }
          {regenerate && (
            <div className="btn-regenerate">
              <Button onClick={() => makeApiRequestStreaming(true)}>
                <AutorenewIcon
                  className="font-20"
                  style={{ transform: "rotate(75deg)" }}
                />
                Try Again
              </Button>
            </div>
          )}
          <div className="like-dislike text-right">
            <div className="text-right" style={{ position: "relative" }}>
              <span style={{ position: "absolute", right: "90px" }}>Rate this Response </span>
              <button onClick={() => handleLike(-1)}>
                <SentimentVeryDissatisfiedIcon className={rating === -1 ? "text-primary font-20" : "font-20"} />
              </button>
              <button onClick={() => handleLike(0)}>
                <SentimentNeutralIcon className={rating === 0 ? "text-primary font-20" : "font-20"} />
              </button>
              <button onClick={() => handleLike(1)}>
                <SentimentSatisfiedAltIcon className={rating === 1 ? "text-primary font-20" : "font-20"} />
              </button>
            </div>
          </div>

          {/* keeping code for future */}
          {/* {isFeedback && (
            <div className="btn-regenerate">
              <Button
                onClick={handleOpenModal}
                variant="contained"
                color="primary"
              >
                <img src={commentIcon} alt="comment" />
                &nbsp;Leave a comment
              </Button>

              <DynamicModal
                isOpen={isModalOpen}
                onClose={handleCloseModal}
                title={modalTitle}
                content={modalContent}
                actions={modalActions}
              />
            </div>
          )} */}
        </Grid>

        {/* feedback section */}
        {showFeedbackForm && <Grid className="d-flex bg-white feedback-card">
          <Grid
            item
            xs={11}
          >
            {feedbackMessage === "" && <>
              <h5 className="m-0 title">Your feedback makes Companion better. Was this response...</h5>
              <Grid container>

                <Stack spacing={2} direction="row" style={{ background: "transparent" }}>
                  {Object.keys(feedbackForm.tag_ratings).map((key) => (
                    <>
                      <span className="btn btn-dotted" style={{ position: "relative", background: "transparent", margin: "10px 10px 10px 0px" }}>
                        <span className="tag-name">
                          {key} <BootstrapTooltip
                            title={
                              <React.Fragment>
                                {key === "accurate" && <span color="inherit">
                                  <strong>Accuracy</strong> can mean a truthful response, factual consistency, or avoiding errors. Highly inaccurate answers that could be misleading or harmful are particularly important to highlight.
                                </span>}
                                {key === "comprehensive" && <span color="inherit">
                                  <strong>Comprehensiveness</strong> involves whether a response includes sufficient depth and breadth of information, while remaining objective and presenting all relevant perspectives.
                                </span>}
                                {key === "relevant" && <span color="inherit">
                                  <strong>Relevance</strong> refers to a response being on-topic, appropriate for the prompt, easy to understand, and following a clear progression or structure.
                                </span>}
                              </React.Fragment>
                            }
                          >
                            <span style={{ position: "relative" }}>
                              <InfoOutlinedIcon className="tag-info" />
                            </span>
                          </BootstrapTooltip>
                        </span>
                        <span
                        >
                          <button style={{ border: "none", background: "transparent", padding: "0px 0px 0px 20px", color: "#444", minWidth: "55px", position: "relative" }}>
                            {feedbackForm.tag_ratings[key] === -1 && <>
                              <ThumbUpOffAltIcon className="font-20 cursor-pointer icon-left" onClick={() => handleFeedbackTags("like", key, feedbackForm.tag_ratings[key])} />
                              <ThumbDownAlt className="font-20 cursor-pointer icon-right" onClick={() => handleFeedbackTags("dislike", key, feedbackForm.tag_ratings[key])} />
                            </>
                            }
                            {feedbackForm.tag_ratings[key] === 0 && <>
                              <ThumbUpOffAltIcon className="font-20 cursor-pointer icon-left" onClick={() => handleFeedbackTags("like", key, feedbackForm.tag_ratings[key])} />
                              <ThumbDownOffAltIcon className="font-20 cursor-pointer icon-right" onClick={() => handleFeedbackTags("dislike", key, feedbackForm.tag_ratings[key])} />
                            </>
                            }
                            {feedbackForm.tag_ratings[key] === 1 && <>
                              <ThumbUpAltIcon className="font-20 cursor-pointer icon-left" onClick={() => handleFeedbackTags("like", key, feedbackForm.tag_ratings[key])} />
                              <ThumbDownOffAltIcon className="font-20 cursor-pointer icon-right" onClick={() => handleFeedbackTags("dislike", key, feedbackForm.tag_ratings[key])} />
                            </>
                            }
                          </button>
                        </span>
                      </span>
                      {/* </Grid> */}
                    </>
                  ))}
                </Stack>
              </Grid>
              <Grid item xs={12}>
                <div>
                  <TextareaAutosize
                    maxRows={5}
                    minRows={2}
                    aria-label="maximum height"
                    placeholder="Tell us more about this response..."
                    defaultValue=""
                    value={feedbackForm.feedback}
                    onChange={(e) => setFeedbackMsg(e.target.value)}
                    className="feedback-textbox"
                  />
                </div>
              </Grid>
              <Grid item container xs={12}>
                <Button variant="contained" disabled={isSubmit} onClick={() => setFeedback("", "feedback")} className="btn btn-primary mt-1">Submit</Button>
              </Grid>
            </>}

            {feedbackMessage !== "" && <>
              <h5 className="m-0 title">{feedbackMessage}</h5>
            </>}
          </Grid>
          <Grid
            item
            xs={1}
            className="text-right cursor-pointer"
            onClick={closeFeedback}
          >
            <CloseIcon className="text-primary" style={{ fontSize: "1rem" }} />
          </Grid>
        </Grid>}

        {image_details.length > 0 && <Accordion
          onChange={handleImageAccordion}
          expanded={imgExpanded}
          className="answer-wrapper-outer mt-1"
          style={{
            background: "#0062c314",
            borderRadius: "10px",
            boxShadow: "none",
            padding: "0px"
          }}
        >
          <AccordionSummary
            expandIcon={<ExpandMoreIcon className="f-secondary" />}
            aria-controls="panel1a-content"
            id="panel1a-header"
            style={{
              margin: "0px"
            }}
          >
            Related Images
          </AccordionSummary>
          <AccordionDetails>
            <Grid container spacing={2}>
              {image_details.map((data, index) => (
                <>
                  {(index === 0 || image_details[index - 1].document_name !== data.document_name) && <Grid sm={12}>
                    <div style={{
                      paddingLeft: "15px"
                    }} className="mt-2">

                      <h4>{data.document_name}</h4>
                      <p className="mt-1" style={{
                        display: "block"
                      }}>
                        <span className="text-center" style={{
                          width: "80px",
                          borderRadius: "100px",
                          background: "#dde5ed",
                          padding: "3px 10px"
                        }}>{data?.source}</span>
                        <span className="text-center f-primary ml-15" style={{
                          width: "160px",
                        }}>
                          <a href={data.document_url} rel="noopener noreferrer" target="_blank" style={{
                            position: "relative"
                          }}> View Document <OpenInNewIcon style={{
                            position: "absolute",
                            fontSize: "15px",
                            top: "2px"
                          }} /></a></span>
                      </p>
                    </div>
                  </Grid>}
                  <Grid sm={6} item >
                    <div style={{
                      position: "relative"
                    }}>
                      <div className="img-wrapper">
                        <div style={{
                          position: "relative"
                        }}>
                          <img src={data.url} alt="response image" className="image-response" />
                          <span className="image-expand">
                            <OpenInFullIcon className="image-expand-icon" onClick={() => showImageDetails(data, index)} />
                          </span>
                        </div>
                      </div>
                    </div>
                    <div>
                      <figcaption className="image-caption">{data.caption}</figcaption>
                    </div>
                  </Grid>
                </>
              ))}
            </Grid>
          </AccordionDetails>
        </Accordion>}

        {Object.keys(imageData).length > 0 && <>
          <DynamicModal
            isOpen={isModalOpen}
            onClose={handleCloseModal}
            title={modalTitle}
            content={modalContent}
            actions={modalActions}
            source="image"
          />
        </>}


        {sourceObj.length > 0 && <Accordion
          onChange={handleChange}
          expanded={isExpanded}
          // onChange={handleAccorcionChange(`panel${msg_id}`)}
          ref={accordionRef}
          className="answer-wrapper-outer"
        >
          <AccordionSummary
            // expandIcon={<RemoveIcon className="f-secondary" />}
            aria-controls="panel1a-content"
            id="panel1a-header"
            style={{ padding: "0px", margin: "0px" }}
          >
            <div className="question-style m-0" style={{ margin: "0px" }}>
              {isExpanded ? "Hide Source Details" : "Show Source Details"}
              {isExpanded ? <RemoveIcon className="f-secondary" style={{
                position: "absolute",
                top: "auto",
                marginLeft: "10px"
              }} /> : <AddIcon className="f-secondary" style={{
                position: "absolute",
                top: "auto",
                marginLeft: "10px"
              }} />}
            </div>
          </AccordionSummary>
          <AccordionDetails style={{
            padding: "0px"
          }}>
            <div
              sm={12}
              className="faq-prompt d-block source-prompt"
              container
              justifyContent="center"
              alignItems="center"
              ref={selectRef}
              style={{ padding: "0px" }}
            >
              <div>
                {sourceObj.map((source) => (
                  <>
                    <Accordion
                      onChange={() => handleSourceAccordion(source)}
                      expanded={Boolean(source.isExpanded)}
                      // onChange={handleAccorcionChange(`panel${msg_id}`)}
                      ref={accordionRef}
                      className="answer-wrapper-outer mt-1"
                      style={{
                        background: "#0062c314",
                        borderRadius: "10px",
                        boxShadow: "none",
                        padding: "0px"
                      }}
                    >
                      <AccordionSummary
                        expandIcon={<ExpandMoreIcon className="f-secondary" />}
                        aria-controls="panel1a-content"
                        id="panel1a-header"
                        style={{
                          margin: "0px"
                        }}
                      >
                        <div
                          sm={12}
                          className="faq-prompt d-block source-prompt"
                          container
                          justifyContent="center"
                          alignItems="center"
                          ref={selectRef}
                        >
                          <Grid container spacing={0}>
                            <Grid sm={12}>
                              <h5 className="font-12">
                                {source?.ChunkNumber}
                                {type === "upload_doc" && (
                                  <span className="ml-15">{trimDocId(source?.DocumentName)}</span>
                                )}
                                {type === "" && <span className="ml-15">{source?.DocumentName}</span>}
                              </h5>
                            </Grid>
                          </Grid>
                        </div>
                      </AccordionSummary>
                      <AccordionDetails>
                        <div >
                          <span className="text-center" style={{
                            width: "80px",
                            borderRadius: "100px",
                            background: "#dde5ed",
                            padding: "3px 10px"
                          }}>{source?.flag}</span>
                          <span className="text-center f-primary ml-15" style={{
                            width: "160px",
                          }}>
                            <a href={source.url} rel="noopener noreferrer" target="_blank" style={{
                              position: "relative"
                            }} className="source-link" id={msg_id + "c-" + source?.ChunkNumber}> View Document <OpenInNewIcon style={{
                              position: "absolute",
                              fontSize: "15px",
                              top: "2px"
                            }} /></a></span>
                          {source.author !== "Not Available" && <span className="text-center" style={{
                            padding: "3px",
                            marginLeft: "25px"
                          }}>Authors: {source?.author}</span>}
                        </div>
                        {typeof (source.content) === "object" && source.content.map((data) => (
                          <>
                            <div className="mt-2" style={{
                              display: "flex"
                            }} id={msg_id + "c-" + data.tag}>
                              <div className="text-center text-primary" style={{
                                textTransform: "uppercase",
                                textDecoration: "underline",
                                textUnderlineOffset: "5px",
                                width: "50px",
                                fontWeight: 500
                              }} >{data?.tag}</div>
                              <div className="ml-15">
                                <span className="source-content">{data?.source}</span></div>
                            </div>
                            <div>

                              <div style={{ marginLeft: "35px", marginTop: "10px", fontWeight: 500, display: "block" }}>
                                <a className="source-link" rel="noopener noreferrer" target="_blank" href={source.url + "#page=" + data?.pageNumber} >pg. {data?.pageNumber} <OpenInNewIcon className="" style={{
                                  position: "absolute",
                                  marginLeft: "5px",
                                  fontSize: "17px"
                                }} /></a>
                              </div>
                            </div>
                          </>
                        ))}

                        {typeof (source.content) === "string" && source.content && <div>
                          <p style={{ display: "block" }}>
                            DOCUMENT CLIP(S)
                          </p>
                          <p className="source-block">
                            <span>p. {source?.PageNumber} : </span>
                            {source?.content}
                          </p>
                        </div>}

                      </AccordionDetails>
                    </Accordion>
                  </>
                ))}
              </div>
            </div>
          </AccordionDetails>
        </Accordion>}
      </Card>
    </Stack>
  );
};
