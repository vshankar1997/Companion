import "./UploadDocuments.css";
import React, { useEffect, useRef, useState } from "react";
import { Box, Button, Grid, Container, Stack, Avatar, Card, CardContent } from "@mui/material";
import { api } from "../../services/api";
import axios from "axios";
import { useSnackbar } from "notistack";
import AttachFileIcon from "@mui/icons-material/AttachFile";
import { UserChatMessage } from "../UserChatMessage";
import { Answer } from "../KnowledgeBase/Answer";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { Summary } from "./Summary";
import AddIcon from "@mui/icons-material/Add";
import { SummaryProgress } from "./SummaryProgress";
import { useBackgroundColor } from "../../BackgroundContext";
import { AnswerStreaming } from "../KnowledgeBase/AnswerStreaming";
import BlinkingDots from "../KnowledgeBase/BlinkingDots";
import SmartToyOutlinedIcon from "@mui/icons-material/SmartToyOutlined";
import promptIcon from "../../assets/images/MaskedIcon.png"
const FilePrompt = (props) => {
  const { enqueueSnackbar } = useSnackbar();
  const [isSummary, setIsSummary] = useState(false);
  const [isUpdate, setIsUpdate] = useState(false);
  const answerBlock = useRef(null)
  let sessionId = props.session_id;
  const notifyUser = (msg, variant) => {
    enqueueSnackbar(msg, {
      variant,
      anchorOrigin: {
        vertical: "top",
        horizontal: "right",
      },
    });
  };

  const { historyList, setHistoryList, user_bu, setIsChat } = useBackgroundColor();

  useEffect(() => {
    props.setUploadState(props.uploadState);
  }, [isUpdate, props]);

  useEffect(() => {
    if(answerBlock.current && (props.scrollDirection !== "up")) {
      answerBlock.current.scrollTop = answerBlock.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [props]);

  const updateState = (msg_id, value) => {
    Object.keys(props.uploadState).forEach((obj) => {
      if (props.uploadState[obj].msg_id === msg_id) {
        props.uploadState[obj].rating = value;
      }
    });
    props.setUploadState(props.uploadState);
    setIsUpdate(!isUpdate);
  };

  const makeApiRequest = async (regenerate = false) => {
    setIsChat(true);
    if (!regenerate && props.currentuploadState.question === "") {
      return 0;
    }
    setIsSummary(false);
    let requestData = {
      prompt: props.currentuploadState.question,
      session_id: sessionId,
      email: localStorage.getItem("email"),
      regenerate: regenerate,
      user_bu: user_bu,
      is_upload: true
    };
    let ans1 = {
      ...props.currentuploadState,
      isLoading: true,
      source: [],
    };

    props.setCurrentuploadState(ans1);
    var tempState = [...props.uploadState, { ...ans1 }];
    props.setUploadState(tempState);
    props.setUploadStatus(1);

    try {
      let url = `${process.env.REACT_APP_API_URL}stream_data/`;
      const response = await fetch(url, {
        method: "POST",
        body: JSON.stringify(requestData),
        headers: {
          "Content-Type": "application/json",
        },
      });
      const uploadReader = response.body.getReader();
      let result = "";
      let msg_id = "";
      while (true) {
        const { done, value } = await uploadReader.read();
        if (done) break;
        if (new TextDecoder().decode(value) !== "None") {
          let str = new TextDecoder().decode(value);
          str = str.replace(/"/g, '<double>');
          const jsonObjects = str.split("@@\n\n").filter(Boolean);
          if(jsonObjects.length === 1 && JSON.parse(jsonObjects[0].replace(/'/g, '"')).msg_id) {
            msg_id = JSON.parse(jsonObjects[0].replace(/'/g, '"'))?.msg_id;
            break;
          }
          jsonObjects.forEach((jsonString) => {
            try {
              if (jsonString.substring(10, 16) === "answer") {
                let obj = JSON.parse(jsonString.replace(/'/g, '"'))?.data;
                obj = obj.replace(/<quote>/g, "'");
                obj = obj.replace(/<double>/g, "\"");
                result += obj;
                result = result.replace(/<quote>/g, "'");
                result = result.replace(/<double>/g, "\"");
                let ans = {
                  ...ans1,
                  answers: result,
                  isLoading: false,
                  source: [],
                  msg_id: "",
                  rating: "",
                };

                let cur_ans_obj = {
                  ...props.currentuploadState,
                  isLoading: false,
                };
                props.setCurrentuploadState(cur_ans_obj);
                tempState = [...props.uploadState, { ...ans }];
                props.setUploadState(tempState);
              } else {
                if (JSON.stringify(jsonString)) {
                  msg_id = JSON.parse(jsonString)?.data;
                }
              }
              return true;
            } catch (error) {
              return false;
            }
          });
        }
      }

      try {
        let url = `${process.env.REACT_APP_API_URL}chat_prompt/${msg_id}`;
        const response = await api.get(url);
        let resData = response.data;
        props.setChatTitle(resData.data?.chat_title);
        tempState.forEach((item) => {          
          if (item.msg_id === "") {
            item.isLoading = false;
            item.created_at = resData.data?.created_at;
            item.answers = resData.data?.message;
            item.msg_id = resData.data?._id;
            item.source = resData.data?.source;
            item.rating = resData.data?.rating || "";
          }
        });
        props.setUploadState(tempState);
        if(answerBlock.current) {
          answerBlock.current.scrollTop = answerBlock.current.scrollIntoView({ behavior: "smooth" });
        }
      } catch (error) {
        // Handle errors
        if (axios.isAxiosError(error)) {
          console.error("Axios Error:", error.message);
        } else {
          console.error("Error:", error.message);
        }
      }

      let ans = {
        ...props.currentuploadState,
        answers: response.data.data?.message,
        isLoading: false,
        source: response.data.data?.source,
        msg_id: response.data.data?.msg_id,
        rating: (response.data.data.rating || response.data.data.rating === 0) ? response.data.data.rating : "",
      };

      let tempState = [...props.uploadState, { ...ans }];
      props.setUploadState(tempState);
      ans = {
        ...props.currentuploadState,
        question: "",
      };
      props.setCurrentuploadState(ans);
    } catch (error) {
      let ans = {
        ...props.currentuploadState,
        isLoading: false,
      };
      props.setCurrentuploadState(ans);
      enqueueSnackbar("Something went wrong. Please try again.", {
        variant: "warning",
        anchorOrigin: {
          vertical: "top",
          horizontal: "right",
        },
      });
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

  const CheckboxButton = ({ label, isChecked, onChange }) => {
    return (
      <label
        className={`checkbox-button summary-option ${
          isChecked ? "checked" : ""
        } ${label !== "Summarize uploaded document" ? "disabled" : ""}`}
      >
        <input
          type="checkbox"
          checked={isChecked}
          onChange={onChange}
          disabled={label === "Summarize uploaded document" ? false : true}
        />
        {label}
      </label>
    );
  };

  const [checkboxes, setCheckboxes] = useState({
    checkbox1: true,
    checkbox2: false,
    checkbox3: false,
    checkbox4: false,
    checkbox5: false,
  });

  /*
  - Function to handle the checkbox change for generating summary   
  - Author - Vinay K M
  - Updated by - Vinay K M
  */
  const handleCheckboxChange = (checkbox) => {
    setCheckboxes((prevCheckboxes) => ({
      ...prevCheckboxes,
      [checkbox]: !prevCheckboxes[checkbox],
    }));
  };

  /*
  - Function send prompt request for server and update the UI accordingly before and after the response.
  - Author - Vinay K M
  - Updated by - Vinay K M
  */
  const generateResponse = async (regenerate = false, type="summary") => {
    if(type === "summary") setIsSummary(true);
    props.setActiveState(3);
    let stepComplete = props.uploadStatus === 0 ? true : false;
    props.setStepCompleted(2);
    let ans1 = {
      ...props.currentuploadState,
      question: type === "summary" ? "Summarize uploaded document" : "Compare the uploaded documents",
      isLoading: true,
    };

    props.setCurrentuploadState(ans1);
    let tempState = [{ ...ans1 }];
    props.setUploadState(tempState);
    props.setUploadStatus(1);
    let requestData = {
      prompt: type === "summary" ? "Summarize uploaded document" : "Compare the uploaded documents",
      session_id: props.session_id,
      email: localStorage.getItem("email"),
      regenerate: regenerate ? true : false,
      is_upload: true,
      user_bu: user_bu,
    };

    if (stepComplete) {
      let o_historyList = historyList;
      let new_chat = {
        chat_title: "New Chat",
        session_id: "",
        isUpload: true,
      };
      o_historyList.today?.unshift(new_chat);
      setHistoryList(o_historyList);
    }

    try {
      let url = `${process.env.REACT_APP_API_URL}stream_data/`;
      const response = await fetch(url, {
        method: "POST",
        body: JSON.stringify(requestData),
        headers: {
          "Content-Type": "application/json",
        },
      });
      props.setActiveState(3);
      props.setStepCompleted(3);
      const uploadReader = response.body.getReader();

      let result = "";
      let msg_id = "";
      while (true) {
        if(type === "summary") setIsSummary(false);
        const { done, value } = await uploadReader.read();
        if (done) break;
        if (new TextDecoder().decode(value) !== "None") {
          let str = new TextDecoder().decode(value);
          str.replace(/"/g, '<double>');
          const jsonObjects = str.split("@@\n\n").filter(Boolean);
          if(jsonObjects.length === 1 && JSON.parse(jsonObjects[0].replace(/'/g, '"')).msg_id) {
            msg_id = JSON.parse(jsonObjects[0].replace(/'/g, '"'))?.msg_id;
            break;
          }
          jsonObjects.map((jsonString) => {
            try {
              if (jsonString.substring(10, 16) === "answer") {
                let obj = JSON.parse(jsonString.replace(/'/g, '"'))?.data;
                obj = obj.replace(/<quote>/g, "'");
                obj = obj.replace(/<double>/g, "\"");
                result += obj;
                result = result.replace(/<quote>/g, "'");
                result = result.replace(/<double>/g, "\"");
                let ans = {
                  ...ans1,
                  answers: result,
                  isLoading: false,
                  source: [],
                  msg_id: "",
                  rating: "",
                };

                let cur_ans_obj = {
                  ...props.currentuploadState,
                  isLoading: false,
                };
                props.setCurrentuploadState(cur_ans_obj);
                tempState = [...props.uploadState, { ...ans }];
                props.setUploadState(tempState);
              } else {
                if (JSON.stringify(jsonString)) {
                  msg_id = JSON.parse(jsonString)?.data;
                }
              }
              return true;
            } catch (error) {
              return false;
            }
          });
        }
      }

      let tempState1 = [...tempState, { ...ans1 }];
      props.setUploadState(tempState1);
      ans1 = {
        ...props.currentuploadState,
        question: "",
      };
      props.setCurrentuploadState(ans1);
      if(type === "summary") setIsSummary(false);

      let s_id = ""
      let title = ""
      try {
        let url = `${process.env.REACT_APP_API_URL}chat_prompt/${msg_id}`;
        const response = await api.get(url);
        let resData = response.data;
        s_id = resData.data?.session_id;
        title = resData.data?.chat_title;
        props.setChatTitle(resData.data?.chat_title);
        tempState.forEach(item => {
          if (item.msg_id === "") {
            item.isLoading = false;
            item.created_at = resData.data?.created_at;
            item.answers = resData.data?.message;
            item.msg_id = resData.data?._id;
            item.source = resData.data?.source;
            item.rating = resData.data?.rating || "";
          }
        });

        if (stepComplete) {
          let o_historyList = historyList;
          let new_chat = {
            chat_title: title,
            session_id: s_id,
            isUpload: true,
          };
          o_historyList.today?.unshift(new_chat);
          setHistoryList(o_historyList);
        }
        props.setUploadState(tempState);
        if(answerBlock.current) {
          answerBlock.current.scrollTop = answerBlock.current.scrollIntoView({ behavior: "smooth" });
        }
      } catch (error) {
        // Handle errors
        if (axios.isAxiosError(error)) {
          console.error("Axios Error:", error.message);
        } else {
          console.error("Error:", error.message);
        }
      }
    } catch (error) {
      notifyUser("Something went wrong. Please try again.", "warning");
      let ans = {
        ...props.currentuploadState,
        isLoading: false,
      };
      props.setCurrentuploadState(ans);
      if(type === "summary") setIsSummary(false);
      if (axios.isAxiosError(error)) {
        // Axios-specific error handling
        console.error("Axios Error:", error.message);
        console.error("Response Data:", error.response?.data);
      } else {
        // General error handling
        console.error("Error:", error.message);
        if(type === "summary") setIsSummary(false);
      }
      if (stepComplete) {
        let o_historyList = historyList;
        o_historyList.today?.shift();
        setHistoryList(o_historyList);
      }
    }
  };
  
  /*
  - Function for back functionality from QA page
  - Author - Vinay K M
  - Updated by - Vinay K M
  */
  const goBack = () => {
    // props.setUploadStatus(0);
    setIsSummary(false);
    if (props.stepCompleted < 3) {
      props.setActiveState(1);
      props.setStepCompleted(1);
    } else {
      props.setActiveState(1);
      props.setStepCompleted(1);
    }
    props.setUploadState([]);
  };

  /*
  - Function to reset the state values for new session
  - Author - Vinay K M
  - Updated by - Vinay K M
  */
  const startNew = () => {
    setIsChat(false);
    props.setUploadStatus(0);
    props.setActiveState(0);
    props.setStepCompleted(0);
    props.setSelectedFiles([]);
    props.setUploadState([]);
  };

  const trimDocId = (docName) => {
    let docContent = docName.split("_@_")[docName.split("_@_").length - 1];
    docContent = docContent.split(".")[0];
    docContent = "_@_" + docContent;
    return docName.replace(docContent, "");
  };

  return (
    <Box>
      <Grid container>
        <Grid item sm={12}>
          <Container maxWidth="xl" className="file-prompt-wrapper ">
            {props.uploadStatus === 1 && (
              <>
                {props.uploadState.length > 0 && <div className="btn-back">
                  <Button
                    variant="text"
                    onClick={goBack}
                    style={{ textTransform: "capitalize", zIndex: "1" }}
                    disabled={
                      (props.activeState === 3 && props.stepCompleted === 2) ||
                      props.currentuploadState.isLoading
                    }
                  >
                    <ArrowBackIcon /> Back
                  </Button>
                </div>}
                <div className="btn-new-prompt">
                  <Button variant="outlined" onClick={startNew}>
                    <AddIcon /> Start a New Prompt
                  </Button>
                </div>
              </>
            )}
            {props.uploadStatus === 0 && (
              <>
                <Grid
                  item
                  sm={12}
                  md={12}
                  sx={{
                    position: "relative",
                  }}
                  className="section-summary-option mt-2 d-none"
                >
                  <div className="text-center">
                    <h3 className="m-0">
                      What would you like to create from your documents?
                    </h3>
                    <p>
                      Select as many options as you would like or add your own
                      prompt in the text field
                    </p>
                  </div>
                  <div className="checkbox-container-row1">
                    <CheckboxButton
                      label="Summarize uploaded document"
                      isChecked={checkboxes.checkbox1}
                      onChange={() => handleCheckboxChange("checkbox1")}
                    />
                    <CheckboxButton
                      label="Similarities + differences between documents"
                      isChecked={checkboxes.checkbox2}
                      onChange={() => handleCheckboxChange("checkbox2")}
                    />
                    <CheckboxButton
                      label="Summarize key themes"
                      isChecked={checkboxes.checkbox3}
                      onChange={() => handleCheckboxChange("checkbox3")}
                    />
                  </div>
                  <Grid container className="mt-1" style={{ gap: "10px" }}>
                    <Grid xs={1} />
                    <Grid xs={4}>
                      <CheckboxButton
                        label="Create a presentation outline"
                        isChecked={checkboxes.checkbox4}
                        onChange={() => handleCheckboxChange("checkbox4")}
                      />
                    </Grid>
                    <Grid xs={4}>
                      <CheckboxButton
                        label="Show me related internal information"
                        isChecked={checkboxes.checkbox5}
                        onChange={() => handleCheckboxChange("checkbox5")}
                      />
                    </Grid>
                    <Grid xs={2} />
                  </Grid>
                  <Grid
                    item
                    sm={12}
                    md={12}
                    sx={{ pt: "0 !important" }}
                    className="text-center mt-1"
                  >
                    <Button
                      variant="contained"
                      size="large"
                      className="btn-rounded"
                      style={{ textTransform: "capitalize" }}
                      // disabled={!isValid}
                      onClick={() => generateResponse(false, "summary")}
                    >
                      Generate A Response
                    </Button>
                  </Grid>
                </Grid>
              </>
            )}

            {props.activeState === 1 && (
              <Grid
                item
                sm={12}
                md={12}
                sx={{ pt: "20% !important" }}
                className="text-center"
              >
                <Button
                  variant="contained"
                  size="large"
                  className="btn-rounded"
                  style={{ textTransform: "capitalize" }}
                  onClick={() => generateResponse(false, 'summary')}
                >
                  <img src={promptIcon} style={{marginRight: "8px"}} alt="prompt icon" /> Summarize Uploads
                </Button>
                {props.files.length > 1 && <Button
                  variant="contained"
                  size="large"
                  className="btn-rounded ml-2"
                  style={{ textTransform: "capitalize", marginLeft: "15px" }}
                  onClick={() => generateResponse(false, "compare")}
                >
                  <img src={promptIcon} style={{marginRight: "8px"}} alt="prompt icon"/> Compare Documents
                </Button>}
              </Grid>
            )}
            {props.uploadStatus === 1 && props.files.length > 0 && props.uploadState.length > 0 && (
              <p className="text-right mt-0 upload-section doc-list">
                <span
                  style={{
                    marginRight: "5px",
                  }}
                  className="text-muted"
                >
                  <AttachFileIcon
                    className="text-primary"
                    style={{ fontSize: "12px" }}
                  />
                </span>
                {Object.keys(props.files).map(
                  (key) =>
                    key < 2 && (
                      <span
                        key={key}
                        style={{
                          marginRight: "10px",
                          fontWeight: 500,
                        }}
                      >
                        <span className="text-muted text-small">
                          {trimDocId(props.files[key]?.name)}
                        </span>
                        {key < Object.keys(props.files).length - 1 && (
                          <span className="text-muted">,</span>
                        )}
                        {}
                      </span>
                    )
                )}
                {Object.keys(props.files).length > 2 && (
                  <span
                    style={{
                      marginLeft: "5px",
                      fontWeight: "bold",
                      display: "inline-block",
                    }}
                    className="text-muted"
                  >
                    <u>+{Object.keys(props.files).length - 2} More</u>
                  </span>
                )}
              </p>
            )}
            {Object.keys(props.uploadState).length > 0 &&
              !isSummary &&
              props.uploadStatus > 0 &&
              props.uploadState?.map((qa, index) => (
                <Box
                  key={index}
                  sx={{
                    flexGrow: "1",
                    // maxHeight: "1024px",
                    width: "100%",
                    // overflowY: "auto",
                    px: 0,
                    display: "grid",
                    flexDirection: "column",
                  }}
                >
                  <Grid>
                    <Grid
                      item
                      sx={{
                        display: "flex",
                        justifyContent: "flex-start",
                        maxWidth: "100%",
                        marginLeft: "auto",
                      }}
                    >
                      <Grid container style={{ justifyContent: "start" }}>
                        <Grid item sm={10.25}>
                          {index ===
                            Object.keys(props.uploadState).length - 1 && (
                            <div ref={props.messagesContainerRef}>
                              <UserChatMessage
                                message={qa.question}
                                readOnly={false}
                                files={qa.summary ? props.files : ""}
                              />
                            </div>
                          )}
                          {index !==
                            Object.keys(props.uploadState).length - 1 && (
                            <UserChatMessage
                              message={qa.question}
                              readOnly={false}
                              files={qa.summary ? props.files : ""}
                            />
                          )}
                        </Grid>
                      </Grid>
                    </Grid>
                    <Grid
                      item
                      sx={{
                        marginBottom: "10px",
                        maxWidth: "90%",
                        display: "flex",
                        minWidth: "500px",
                      }}
                      className="answer-font"
                    >
                      {typeof qa.answers === "object" && (
                        <Box>
                          <Summary
                            key={index}
                            answer={qa.answers}
                            sources={qa.source}
                          />
                        </Box>
                      )}
                      {qa.answers && typeof qa.answers === "string" && (
                        <Box>
                          {qa.msg_id === "" && <AnswerStreaming
                              answer={qa.answers}
                            />}
                            {/* {Object.keys(props.uploadState) - 1 +""+ index} */}
                            {qa.msg_id !== "" && <Answer
                              regenerate={
                                Object.keys(props.uploadState)?.length - 1 === index ? true : false
                              }
                              answer={qa.answers}
                              sources={qa.source ? qa.source : []}
                              msg_id={qa.msg_id}
                              rating={(qa.rating || qa.rating === 0) ? qa.rating : ""}
                              isFeedback={true}
                              updateState={updateState}
                              type="upload_doc"
                              makeApiRequest={makeApiRequest}
                              makeApiRequestStreaming={props.makeFileApiRequest}
                            />}
                            <span ref={answerBlock}></span>
                        </Box>
                      )}
                    </Grid>
                  </Grid>
                </Box>
              ))}
            {props.currentuploadState.isLoading && !isSummary && (
              <Stack
              direction="row"
              spacing={1}
              className="animate__animated animate__fadeInUp answer-wrapper"
            >
              <Avatar sx={{ background: (theme) => theme.palette.primary.main }}>
                <SmartToyOutlinedIcon />
              </Avatar>
              <Card
                variant="elevation"
                style={{ background: "transparent", boxShadow: "none" }}
              >
                <CardContent
                  sx={{
                    background: "rgb(249, 249, 249)",
                    borderRadius: 2,
                    boxShadow: "0px 2px 1px -1px rgba(0,0,0,0.2), 0px 1px 1px 0px rgba(0,0,0,0.14), 0px 1px 3px 0px rgba(0,0,0,0.12)"
                  }}
                  className="copyableCard answer-border"
                >
                  <BlinkingDots count={1} />
                </CardContent>
              </Card>
            </Stack>
            )}
            {isSummary && <SummaryProgress />}
          </Container>
        </Grid>
      </Grid>
      <Container maxWidth="xl" sm={12} className="first file-prompt mt-1">
        {Object.keys(props.uploadState).length === 0 && (
          <Box display="flex" alignItems="center" width="100%" justifyContent="center">
            <span className="prompt-devider" style={{
              bottom: "150px"
            }}>Or enter your own prompt</span>
          </Box>
        )}
        {Object.keys(props.uploadState).length > 0 && (
          <Grid
            container
            sx={{
              pb: "0px",
            }}
          >
            <Grid
              item
              sm={12}
              md={12}
              container
              justifyContent="flex-end"
              className="btn-regenerate"
            >
              <Button variant="contained" sx={{ visibility: "hidden" }}>
                Regenerate
              </Button>
            </Grid>
          </Grid>
        )}

        <Grid
          container
          justifyContent="center"
          alignItems="center"
          spacing={2}
          sx={{ position: "sticky", bottom: "0px" }}
        ></Grid>
      </Container>
    </Box>
  );
};

export default FilePrompt;
