import React, { useEffect, useRef, useState } from "react";
import {
  Box,
  Button,
  Grid,
  IconButton,
  TextField,
  Container,
  styled,
  InputAdornment,
  Stack,
  Card,
  CardContent,
} from "@mui/material";
import SendIcon from "@mui/icons-material/Send";
import { UserChatMessage } from "../UserChatMessage";
import { Answer } from "../KnowledgeBase/Answer";
import Tooltip, { TooltipProps, tooltipClasses } from "@mui/material/Tooltip";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import { useNavigate } from "react-router-dom";
import { api } from "../../services/api";
import axios from "axios";
import { useSnackbar } from "notistack";
import AddIcon from "@mui/icons-material/Add";
import { useBackgroundColor } from "../../BackgroundContext";
import { useLocation } from "react-router-dom";
import "../KnowledgeBase/KnowledgeBase.css";
import AttachFileIcon from "@mui/icons-material/AttachFile";
import BlinkingDots from "../KnowledgeBase/BlinkingDots";
import { AnswerStreaming } from "../KnowledgeBase/AnswerStreaming";
import answerIcon from "../../assets/images/Avatar.png"

const PromptHistory = () => {
  const { setNewBackgroundColor, h_session_id, user_bu, setUser_bu, setIsChat, setOpenDocList, isGetDocs, setIsGetDocs, setBuSelected } = useBackgroundColor();
  setNewBackgroundColor("main-bg-linear");
  const messagesContainerRef = useRef(null);
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const [isUpdate, setIsUpdate] = useState(0);
  const [isUpdateBU, setIsUpdateBU] = useState(false);
  const [sessionId, setSessionId] = useState(h_session_id);
  const [type, setType] = useState("knowledgebase");
  const [state, setState] = useState([]);
  const [uploadFiles, setUploadFiles] = useState([]);
  const location = useLocation();
  const [isAutoScroll, setIsAutoScroll] = useState(false);
  const [chatTitle, setChatTitle] = useState(false);

  useEffect(() => {
    setUser_bu(user_bu)
  }, [isUpdateBU]);

  useEffect(() => {
    const historyData = async () => {
      setIsBlur(true);
      setState([]);
      setIsChat(true);
      setUploadFiles([]);
      try {
        let s_id =
          h_session_id === ""
            ? location.pathname.split("/")[
            location.pathname.split("/").length - 1
            ]
            : h_session_id;
        let url = `${process.env.REACT_APP_API_URL}config/history/${s_id}`;
        setSessionId(s_id);
        const response = await api.get(url);
        setState(response.data.data);
        setChatTitle(response.data?.chat_name);
        setIsBlur(false);
        window.setTimeout(() => {
          setUser_bu(response.data.user_bu);
          setBuSelected(response.data.user_bu);
        }, 300);
        setIsUpdateBU(!isUpdateBU);
        if (response.data?.files.length > 0) {
          setType("uploadDoc");
          setUploadFiles(response.data.files);
        } else {
          setType("knowledgebase");
        }
        window.setTimeout(() => {
          // const element = document.getElementById("query-bar");
          const element = document.getElementById("last-source");
          if (element) {
            element.scrollIntoView({ behavior: "auto", block: "end" });
          }
        }, 500);
      } catch (error) {
        let ans = {
          ...currentState,
          isLoading: false,
        };
        setCurrentState(ans);
        enqueueSnackbar("Something went wrong. Please try again.", {
          variant: "warning",
          anchorOrigin: {
            vertical: "top",
            horizontal: "right",
          },
        });
        setIsBlur(false);
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
    historyData();
  }, [h_session_id]);

  const [sectionHeight, setSectionHeight] = useState("");
  const [prePrompt, setPrePrompt] = useState("");
  const [isBlur, setIsBlur] = useState(false);
  const appBarHeight = 80;
  const [currentState, setCurrentState] = useState({
    prompt: "",
    message: "",
    isLoading: false,
    rating: "",
    _id: "",
  });

  const handleQuestionChange = (event) => {
    setCurrentState({
      ...currentState,
      question: event.target.value,
    });
  };
  const updateState = (_id, value) => {
    Object.keys(state).forEach((obj) => {
      if (state[obj]._id === _id) {
        state[obj].rating = value;
      }
    });
    setState(state);
    setIsUpdate(!isUpdate);
  };
  const scrollToBottom = () => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollIntoView({ behavior: "smooth" });
    }
  };
  useEffect(() => {
    if (!(isAutoScroll && scrollDirection === "up")) {
      scrollToBottom();
    }
    setSectionHeight(`calc(100vh - ${appBarHeight * 3 - 10}px)`);
  }, [state]);

  const sectionRef = useRef(null);
  const [scrollDirection, setScrollDirection] = useState(null);
  const [lastScrollTop, setLastScrollTop] = useState(0);

  useEffect(() => {
    const section = sectionRef.current;
    const handleScroll = () => {
      const scrollTop = section.scrollTop;
      if (scrollTop > lastScrollTop) {
        setScrollDirection('down');
      } else if (scrollTop < lastScrollTop) {
        setScrollDirection('up');
      }
      setLastScrollTop(scrollTop <= 0 ? 0 : scrollTop);
    };
    section.addEventListener('scroll', handleScroll);
    return () => section.removeEventListener('scroll', handleScroll);
  }, [lastScrollTop]);

  /*
- Function to start new session on click of new prompt button
- Author - Vinay K M
- Updated by - Vinay K M
*/
  useEffect(() => {
    setState(state);
  }, [isUpdate]);

  const BootstrapTooltip = styled(({ className, ...props }: TooltipProps) => (
    <Tooltip {...props} arrow classes={{ popper: className }} />
  ))(({ theme }) => ({
    [`& .${tooltipClasses.arrow}`]: {
      color: theme.palette.common.black,
    },
    [`& .${tooltipClasses.tooltip}`]: {
      backgroundColor: theme.palette.common.black,
    },
  }));

  /*
  - Function to reset the state values for new session
  - Author - Vinay K M
  - Updated by - Vinay K M
  */
  const startNew = () => {
    setState([]);
    setSessionId("");
    navigate("/prompt");
  };

/*
- Function to send prompt request and get the response answer data with streaming
- Update current state and set loader until we get the response and then update main state
- Author - Vinay K M
- Updated by - Vinay K M
*/
  const makeApiRequestStreaming = async (regenerate = false) => {
    setIsChat(true);
    if (!regenerate && currentState.question === "") {
      return 0;
    }
    let requestData = {
      prompt: regenerate ? prePrompt : currentState.question,
      session_id: sessionId,
      email: localStorage.getItem("email"),
      type: "internal",
      regenerate: regenerate,
      user_bu: user_bu,
      is_upload: type === "knowledgebase" ? false : true
    };
    let ans1 = {
      ...currentState,
      isLoading: true,
      prompt: regenerate ? "" : currentState.question,
      source: [],
      msg_id: "",
      image_details: [],
      get_only_images: false
    };

    setCurrentState(ans1);
    var tempState = [...state, { ...ans1 }];
    setState(tempState);
    try {
      let url = `${process.env.REACT_APP_API_URL}stream_data/`;
      const response = await fetch(url, {
        method: "POST",
        body: JSON.stringify(requestData),
        headers: {
          "Content-Type": "application/json",
        },
      });

      const reader = response.body.getReader();
      setIsAutoScroll(true);
      let result = "";
      let msg_id = "";
      let srcObj = [];
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        if (new TextDecoder().decode(value) !== "None") {
          let str = new TextDecoder().decode(value);
          const jsonObjects = str.split("@@\n\n").filter(Boolean);
          if (jsonObjects.length === 1 && JSON.parse(jsonObjects[0].replace(/'/g, '"')).msg_id) {
            msg_id = JSON.parse(jsonObjects[0].replace(/'/g, '"')).msg_id;
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
                  message: result,
                  isLoading: false,
                  source: [],
                  msg_id: "",
                  rating: "",
                  image_details: [],
                  get_only_images: false
                };

                let cur_ans_obj = {
                  ...currentState,
                  isLoading: false,
                };
                setCurrentState(cur_ans_obj);
                tempState = [...state, { ...ans }];
                setState(tempState);
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

      let s_id = ""
      try {
        let url = `${process.env.REACT_APP_API_URL}chat_prompt/${msg_id}`;
        const response = await api.get(url);
        let resData = response.data;
        setIsAutoScroll(false);
        s_id = resData.data?.session_id;
        tempState.forEach(item => {
          if (item.msg_id === "") {
            item.prompt = currentState.question;
            item.isLoading = false;
            item.created_at = resData.data?.created_at;
            item.message = resData.data?.message;
            item.msg_id = resData.data?._id;
            item.source = resData.data?.source;
            item.rating = resData.data?.rating || "";
            item.image_details = resData.data?.image_details || [];
            item.get_only_images = resData.data?.get_only_images || false;
          }
        })
        setState(tempState);
      } catch (error) {
        // Handle errors
        if (axios.isAxiosError(error)) {
          console.error("Axios Error:", error.message);
        } else {
          console.error("Error:", error.message);
        }
      }
      setSessionId(s_id);
      if (!regenerate) setPrePrompt(currentState.question);
      let ans = {
        ...ans1,
        message: result,
        isLoading: false,
        source: srcObj,
        msg_id: "",
        rating: 0,
      };

      scrollToBottom();
      ans = {
        ...currentState,
        question: "",
      };
      setCurrentState(ans);
    } catch (error) {
      let ans = {
        ...currentState,
        isLoading: false,
      };
      setCurrentState(ans);
      enqueueSnackbar("Something went wrong. Please try again.", {
        variant: "warning",
        anchorOrigin: {
          vertical: "top",
          horizontal: "right",
        },
      });
      if (axios.isAxiosError(error)) {
        console.error("Axios Error:", error.message);
        console.error("Response Data:", error.response?.data);
      } else {
        // General error handling
        console.error("Error:", error.message);
      }
    }
  };

  const trimDocId = (docName) => {
    let docContent = docName.split("_@_")[docName.split("_@_").length - 1];
    docContent = docContent.split(".")[0];
    docContent = "_@_" + docContent;
    return docName.replace(docContent, "");
  };

  const handleDocList = () => {
    setBuSelected(user_bu);
    setIsGetDocs(!isGetDocs);
    setOpenDocList(true);

  }

  return (
    <Box
      sx={{
        backgroundSize: "cover",
        padding: "0",
      }}
    >
      {isBlur && (
        <div
          style={{
            height: "85%",
            width: "100%",
            position: "absolute",
            left: "0px",
            zIndex: "999",
          }}
        ></div>
      )}

      {Object.keys(state).length > 0 && (<div className="chat-title">
        <h6 className="m-0">
          <span>
            {chatTitle ? chatTitle : "New Chat"}
          </span>
          {uploadFiles.length === 0 && <span className="float-right" style={{
            fontSize: "14px"
          }}>
            Collection: <span className="chat-bu-name" onClick={handleDocList}>{user_bu}</span>
          </span>}
        </h6>
      </div>)}
      <Grid
        container
        sx={{
          height: { height: sectionHeight },
          overflow: "auto",
          overflowX: "hidden",
          opacity: isBlur ? "0.5" : "1",
        }}
        className="page-scroller"
        ref={sectionRef}
      >
        <Grid item sm={12}>
          <Container
            maxWidth="xl"
            sx={{ height: `calc(100vh - ${appBarHeight * 4}px)` }}
          >
            <>
              {Object.keys(state).length > 0 && (
                <div className="btn-new-prompt">
                  <Button variant="outlined" onClick={startNew}>
                    <AddIcon /> Start a New Prompt
                  </Button>
                </div>
              )}

              {uploadFiles.length > 0 && (
                <p className="text-right mt-0 doc-list">
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
                  {Object.keys(uploadFiles).map(
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
                            {trimDocId(uploadFiles[key])}
                          </span>
                          {key < Object.keys(uploadFiles).length - 1 && (
                            <span className="text-muted">,</span>
                          )}
                          { }
                        </span>
                      )
                  )}
                  {Object.keys(uploadFiles).length > 2 && (
                    <span
                      style={{
                        marginLeft: "5px",
                        fontWeight: "bold",
                        display: "inline-block",
                      }}
                      className="text-muted"
                    >
                      <u>+{Object.keys(uploadFiles).length - 2} More</u>
                    </span>
                  )}
                </p>
              )}

              <div>
                {Object.keys(state).length > 0 &&
                  state?.map((qa, index) => (
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
                            marginBottom: "0px",
                            maxWidth: "100%",
                            marginLeft: "auto",
                          }}
                        >
                          <Grid
                            container
                            style={{ justifyContent: "start" }}
                            className={
                              uploadFiles.length > 0 && index === 0
                                ? "mt-20"
                                : ""
                            }
                          >
                            <Grid item sm={10.25}>
                              {index === Object.keys(state).length - 1 && (
                                <div ref={messagesContainerRef}>
                                  <UserChatMessage
                                    message={qa.prompt}
                                    readOnly={false}
                                  />
                                </div>
                              )}
                              {index !== Object.keys(state).length - 1 && (
                                <UserChatMessage
                                  message={qa.prompt}
                                  readOnly={false}
                                />
                              )}
                            </Grid>
                          </Grid>
                        </Grid>
                        <Grid
                          item
                          sx={{
                            marginBottom: "20px",
                            maxWidth: "100%",
                            display: "flex",
                            minWidth: "500px",
                          }}
                          className="answer-font"
                        >
                          {qa.message && (
                            <Box>
                              {qa.msg_id === "" && <AnswerStreaming
                                answer={qa.message}
                              />}
                              {qa.msg_id !== "" && <Answer
                                regenerate={
                                  state.length - 1 === index ? true : false
                                }
                                answer={qa.message}
                                sources={qa.source}
                                msg_id={qa._id}
                                rating={(qa.rating || qa.rating === 0) ? qa.rating : ""}
                                isFeedback={qa.showComment ? true : false}
                                updateState={updateState}
                                makeApiRequestStreaming={makeApiRequestStreaming}
                                type={
                                  uploadFiles.length > 0 ? "upload_doc" : ""
                                }
                                feedback={
                                  {
                                    tag_ratings: qa.tag_ratings ? qa.tag_ratings : {},
                                    feedback: qa.feedback ? qa.feedback : ""
                                  }
                                }
                                image_details={qa.image_details}
                                get_only_images= {qa.get_only_images}
                              />}
                            </Box>
                          )}
                        </Grid>
                      </Grid>
                    </Box>
                  ))}
                {currentState.isLoading && state.length > 0 && (
                  <Stack
                    direction="row"
                    spacing={1}
                    className="animate__animated animate__fadeInUp answer-wrapper"
                  >
                    <div>
                      <img alt="answer icon" src={answerIcon} width="32px" height="32px" />
                    </div>
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
              </div>
            </>
          </Container>
        </Grid>
      </Grid>
      <Container maxWidth="xl" sm={12} className="first query-bar">
        {Object.keys(state).length === 0 && (
          <Box display="flex" alignItems="center" width="100%">
            {/* <Divider flexItem style={{ flex: 1, borderColor: "#000" }} /> */}
            <span className="prompt-devider">Or enter your own prompt</span>
            {/* <Divider flexItem style={{ flex: 1, borderColor: "#000" }} /> */}
          </Box>
        )}
        {Object.keys(state).length > 0 && (
          <Grid
            container
            sx={{
              pb: 0,
            }}
          ></Grid>
        )}
        <Grid
          container
          justifyContent="center"
          spacing={2}
          sx={{ position: "sticky", bottom: 0 }}
        >
          <>
            <Grid item sm={12} md={12} sx={{ pt: "0 !important" }}>
              <TextField
                multiline
                fullWidth
                size="medium"
                value={currentState.question}
                onKeyDown={(ev) => {
                  if (ev.key === "Enter" && !ev.shiftKey) {
                    ev.preventDefault();
                    makeApiRequestStreaming(false);
                  }
                }}
                disabled={currentState.isLoading}
                onChange={handleQuestionChange}
                sx={{ background: "#fff", border: "none" }}
                placeholder="Ask me anything..."
                className="custom-placeholder"
                style={{
                  borderRadius: "100px",
                  marginTop: "28px",
                  border: "1px solid #E0E0E0",
                }}
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        disabled={
                          currentState.isLoading || currentState.question === ""
                        }
                      >
                        <SendIcon
                          className="text-primary"
                          onClick={() => makeApiRequestStreaming(false)}
                        />
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <p className="text-center m-0 prompt-footer">
              <span className="text-muted">
                What kinds of prompts can I enter?
              </span>
              <BootstrapTooltip
                title={
                  <React.Fragment>
                    <span color="inherit">
                      There are many ways to write a prompt – from simply asking
                      a question, to requesting Companion to generate content
                      using a new format (lists, bullets, etc.) For best results
                      provide specific and clear instructions in your prompt. To
                      see a list of well-written prompts,&nbsp;
                    </span>
                    <span
                      className="learn-more"
                      onClick={() => navigate("/faq")}
                    >
                      read more
                    </span>
                    .
                  </React.Fragment>
                }
              >
                <span>
                  <InfoOutlinedIcon
                    className="text-muted"
                    style={{ marginTop: "3px" }}
                  />
                </span>
              </BootstrapTooltip>
            </p>
          </>
        </Grid>
      </Container>
    </Box>
  );
};

export default PromptHistory;
