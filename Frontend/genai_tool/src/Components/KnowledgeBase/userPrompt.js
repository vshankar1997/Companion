import "../KnowledgeBase/KnowledgeBase.css";
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
  Avatar,
  Card,
  CardContent,
  // CircularProgress,
} from "@mui/material";
import SendIcon from "@mui/icons-material/Send";
import { UserChatMessage } from "../UserChatMessage";
// import { AnswerLoading } from "./AnswerLoading";
import { Answer } from "./Answer";
import UploadDoc from "../UploadDocuments/UploadDoc";
import Tooltip, { TooltipProps, tooltipClasses } from "@mui/material/Tooltip";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import { useNavigate } from "react-router-dom";
import { api } from "../../services/api";
import axios from "axios";
import { useSnackbar } from "notistack";
import UploadProgress from "../UploadDocuments/UploadProgress";
import FilePrompt from "../UploadDocuments/FilePrompt";
import AddIcon from "@mui/icons-material/Add";
import { useBackgroundColor } from "../../BackgroundContext";
import { useLocation } from "react-router-dom";
import { AnswerStreaming } from "./AnswerStreaming";
import SmartToyOutlinedIcon from "@mui/icons-material/SmartToyOutlined";
import BlinkingDots from "./BlinkingDots";
import FolderOpenIcon from '@mui/icons-material/FolderOpen';

import { Menu, MenuItem } from '@mui/material';
import { ArrowDropDown as ArrowDropDownIcon } from '@mui/icons-material';

const UserPrompt = () => {
  const messagesContainerRef = useRef(null);
  const [sessionId, setSessionId] = useState("");
  const [uploadSessionId, setUploadSessionId] = useState("");
  const [activeState, setActiveState] = useState(0);
  const [stepCompleted, setStepCompleted] = useState(0);
  const appBarHeight = 80;
  const [sectionHeight, setSectionHeight] = useState("");
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploadStatus, setUploadStatus] = useState(0);
  const [isAutoScroll, setIsAutoScroll] = useState(false);
  const [chatTitle, setChatTitle] = useState("New Chat");

  const answerBelow = useRef(null)
  const [currentuploadState, setCurrentuploadState] = useState({
    question: "",
    answers: "",
    isLoading: false,
  });

  const handleFileQuestionChange = (event) => {
    setCurrentuploadState({
      ...currentuploadState,
      question: event.target.value,
    });
  };

  // state for background change React context
  const { setNewBackgroundColor, historyList, setHistoryList, user_bu, setUser_bu, setIsChat, isGetDocs, setIsGetDocs, setOpenDocList, defaultUser_bu, buList, setBuSelected } =
    useBackgroundColor();

  // calculate the amount of pixels for drop file section
  useEffect(() => {
    setSectionHeight(
      activeState === 1
        ? `calc(100vh - ${appBarHeight * 2.5 + 10}px)`
        : `calc(100vh - ${appBarHeight * 3}px)`
    );

    if (activeState >= 2) {
      setUploadPlaceholder("Ask a follow up question...");
    } else {
      setUploadPlaceholder("Ask me anything from document uploaded by you");
    }
  }, [activeState]);

  //calc(100vh - ${appBarHeight * 3.5 - 50}px)
  // useEffect(() => {
  //   const interval = setInterval(() => {
  //     setSentenceIndex((prevIndex) => (prevIndex + 1) % sentences.length);
  //   }, 2000); // Repeat every 2 second (2000 milliseconds)

  //   return () => {
  //     clearInterval(interval); // Clear the interval when the component unmounts
  //   };
  // }, []);

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

  const sectionRef = useRef(null);
  const [scrollDirection, setScrollDirection] = useState(null);
  const [lastScrollTop, setLastScrollTop] = useState(0);
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const [state, setState] = useState([]);
  const [uploadState, setUploadState] = useState([]);
  const [isUpdate, setUpdate] = useState(0);
  const [isScrollUp, setIsScrollUp] = useState(false);
  const [prePrompt, setPrePrompt] = useState("");
  const [uploadPrePrompt, setUploadPrePrompt] = useState("");
  const [uploadPlaceholder, setUploadPlaceholder] = useState(
    "Ask me anything from document uploaded by you"
  );

  const location = useLocation();

  if (state.length === 0 || (uploadState.length === 0 && activeState === 0))
    setNewBackgroundColor("main-bg-single");
  else setNewBackgroundColor("main-bg-linear");
  if (state.length > 0 || activeState > 1)
    setNewBackgroundColor("main-bg-linear");

  // if (activeState === 1 && stepCompleted === 1)
  //   setNewBackgroundColor("main-bg-linear");

  /*
  - Function to start new session on click of new prompt button
  - Author - Vinay K M
  - Updated by - Vinay K M
  */
  useEffect(() => {
    setState(state);
  }, [isUpdate]);

  useEffect(() => {
    startNew();
    setIsChat(false);
  }, [location.pathname]);

  const [currentState, setCurrentState] = useState({
    question: "",
    answers: "",
    isLoading: false,
    rating: "",
    msg_id: "",
  });

  const handleQuestionChange = (event) => {
    setCurrentState({
      ...currentState,
      question: event.target.value,
    });
  };

  const updateState = (msg_id, value) => {
    Object.keys(state).forEach((obj) => {
      if (state[obj].msg_id === msg_id) {
        state[obj].rating = value;
      }
    });
    setState(state);
    setUpdate(!isUpdate);
  };

  const scrollToBottom = () => {
    if (messagesContainerRef.current && !(isAutoScroll && scrollDirection === "up")) {
      messagesContainerRef.current.scrollIntoView({ behavior: "smooth" });
    }
  };

  useEffect(() => {
    const section = sectionRef.current;
    const handleScroll = () => {
      const scrollTop = section.scrollTop;
      if (scrollTop > lastScrollTop) {
        setIsScrollUp(!isScrollUp)
        setScrollDirection('down');
      } else if (scrollTop < lastScrollTop) {
        setIsScrollUp(!isScrollUp)
        setScrollDirection('up');
      }
      setLastScrollTop(scrollTop <= 0 ? 0 : scrollTop);
    };
    section.addEventListener('scroll', handleScroll);
    return () => section.removeEventListener('scroll', handleScroll);
  }, [lastScrollTop]);

  useEffect(() => {
    setIsAutoScroll(isAutoScroll);
    setScrollDirection(scrollDirection);
  }, [isScrollUp]);

  /*
  - Function to send prompt request and get the response answer data - OLD
  - Update current state and set loader until we get the response and then update main state
  - Author - Vinay K M
  - Updated by - Vinay K M
  */

  const makeApiRequest = async (regenerate = false) => {
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
      is_upload: false
    };
    let ans1 = {
      ...currentState,
      isLoading: true,
      question: regenerate ? "" : currentState.question,
      source: [],
    };

    setCurrentState(ans1);
    let tempState = [...state, { ...ans1 }];
    setState(tempState);
    if (sessionId === "") {
      let o_historyList = historyList;
      let new_chat = {
        chat_title: "New Chat",
        session_id: "",
      };
      o_historyList.today?.unshift(new_chat);
      setHistoryList(o_historyList);
    }
    try {
      let url = `${process.env.REACT_APP_API_URL}chat_prompt`;
      const response = await api.post(url, requestData);
      if (sessionId === "") {
        let new_chat = {
          chat_title: response.data.data?.title,
          session_id: response.data.data?.session_id,
        };
        let o_historyList = historyList;
        o_historyList.today?.shift();
        o_historyList.today?.unshift(new_chat);
        setHistoryList(o_historyList);
      }
      setChatTitle(response.data?.chat_title)
      setSessionId(response.data.data?.session_id);
      if (!regenerate) setPrePrompt(currentState.question);
      let ans = {
        ...ans1,
        answers: response.data.data?.message,
        isLoading: false,
        source: response.data.data?.source,
        msg_id: response.data.data?.msg_id,
        rating: (response.data.data.rating || response.data.data.rating === 0) ? response.data.data.rating : "",
      };

      let tempState = [...state, { ...ans }];
      setState(tempState);
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
        // Axios-specific error handling
        console.error("Axios Error:", error.message);
        console.error("Response Data:", error.response?.data);
      } else {
        // General error handling
        console.error("Error:", error.message);
      }
      if (sessionId === "") {
        let o_historyList = historyList;
        o_historyList.today?.shift();
        setHistoryList(o_historyList);
      }
    }
  };

  useEffect(() => {
    if (answerBelow.current && !(isAutoScroll && scrollDirection === "up")) {
      answerBelow.current.scrollTop = answerBelow.current.scrollIntoView({ behavior: "smooth" });
    }
    let height = (state.length === 0 && uploadState.length === 0) ? `calc(100vh - ${appBarHeight * 3 - 60}px)` : `calc(100vh - ${appBarHeight * 3 - 0}px)`
    setSectionHeight(height);
  }, [state, uploadState]);

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
      is_upload: false
    };
    let ans1 = {
      ...currentState,
      isLoading: true,
      question: regenerate ? "" : currentState.question,
      source: [],
      image_details: [],
      get_only_images: false
    };

    setCurrentState(ans1);
    var tempState = [...state, { ...ans1 }];
    setState(tempState);
    if (sessionId === "") {
      let o_historyList = historyList;
      let new_chat = {
        chat_title: "New Chat",
        session_id: "",
      };
      o_historyList.today?.unshift(new_chat);
      setHistoryList(o_historyList);
    }
    setIsAutoScroll(null);
    setScrollDirection("down");
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
                  answers: result,
                  isLoading: false,
                  source: [],
                  msg_id: "",
                  rating: "",
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
      let title = ""
      try {
        let url = `${process.env.REACT_APP_API_URL}chat_prompt/${msg_id}`;
        const response = await api.get(url);
        setIsAutoScroll(false);
        let resData = response.data;
        s_id = resData.data?.session_id;
        title = resData.data?.chat_title;
        setChatTitle(resData.data?.chat_title)
        tempState.forEach(item => {
          if (item.msg_id === "") {
            item.isLoading = false;
            item.created_at = resData.data?.created_at;
            item.answers = resData.data?.message;
            item.msg_id = resData.data?._id;
            item.source = resData.data?.source;
            item.rating = resData.data?.rating || "";
            item.image_details = resData.data?.image_details;
            item.get_only_images = resData.data.get_only_images ? resData.data.get_only_images : false 
          }
        });
        setState(tempState);
      } catch (error) {
        // Handle errors
        if (axios.isAxiosError(error)) {
          console.error("Axios Error:", error.message);
        } else {
          console.error("Error:", error.message);
        }
      }


      if (sessionId === "") {
        let new_chat = {
          chat_title: title,
          session_id: s_id
        };
        let o_historyList = historyList;
        o_historyList.today?.shift();
        o_historyList.today?.unshift(new_chat);
        setHistoryList(o_historyList);
      }
      setSessionId(s_id);
      if (!regenerate) setPrePrompt(currentState.question);
      let ans = {
        ...ans1,
        answers: result,
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
      if (sessionId === "") {
        let o_historyList = historyList;
        o_historyList.today?.shift();
        setHistoryList(o_historyList);
      }
    }
  };

  /*
  - Function to send prompt request from upload doc and get the response answer data
  - Update current state and set loader until we get the response and then update main state in upload doc page
  - Author - Vinay K M
  - Updated by - Vinay K M
  */
  const makeFileApiRequest = async (regenerate = false) => {
    setIsChat(true);
    if (!regenerate && currentuploadState.question === "") {
      return 0;
    }
    let requestData = {
      prompt: regenerate ? uploadPrePrompt : currentuploadState.question,
      session_id: uploadSessionId,
      email: localStorage.getItem("email"),
      regenerate: regenerate,
      user_bu: user_bu,
      is_upload: true
    };
    let ans1 = {
      ...currentuploadState,
      question: regenerate ? "" : currentuploadState.question,
      isLoading: true,
      source: [],
      msg_id: "",
      image_details : [],
      get_only_images: false
    };

    setCurrentuploadState(ans1);
    let tempState = [...uploadState, { ...ans1 }];
    setUploadState(tempState);
    let actState = uploadStatus === 0 ? true : false;
    setActiveState(2);
    if (actState) {
      let o_historyList = historyList;
      let new_chat = {
        chat_title: "New Chat",
        session_id: "",
        isUpload: true,
      };
      o_historyList.today?.unshift(new_chat);
      setHistoryList(o_historyList);
    }
    setUploadStatus(1);
    setScrollDirection("down");
    setIsAutoScroll(null);
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
      setIsAutoScroll(true);
      let result = "";
      let msg_id = "";
      let srcObj = [];
      while (true) {
        const { done, value } = await uploadReader.read();
        if (done) break;
        if (new TextDecoder().decode(value) !== "None") {
          let str = new TextDecoder().decode(value);
          const jsonObjects = str.split("@@\n\n").filter(Boolean);
          if (jsonObjects.length === 1 && JSON.parse(jsonObjects[0].replace(/'/g, '"')).msg_id) {
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
                  ...currentuploadState,
                  isLoading: false,
                };
                setCurrentuploadState(cur_ans_obj);
                tempState = [...uploadState, { ...ans }];
                setUploadState(tempState);
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
      let title = ""
      try {
        let url = `${process.env.REACT_APP_API_URL}chat_prompt/${msg_id}`;
        const response = await api.get(url);
        setIsAutoScroll(false);
        let resData = response.data;
        s_id = resData.data?.session_id;
        title = resData.data?.chat_title;
        setChatTitle(resData.data?.chat_title);
        tempState.forEach(item => {
          if (item.msg_id === "") {
            item.isLoading = false;
            item.created_at = resData.data?.created_at;
            item.answers = resData.data?.message;
            item.msg_id = resData.data?._id;
            item.source = resData.data?.source;
            item.rating = resData.data?.rating || "";
            item.image_details = resData.data?.image_details;
            item.get_only_images = resData.data.get_only_images ? resData.data.get_only_images : false

          }
        });
        setUploadState(tempState);
      } catch (error) {
        // Handle errors
        if (axios.isAxiosError(error)) {
          console.error("Axios Error:", error.message);
        } else {
          console.error("Error:", error.message);
        }
      }

      if (actState) {
        let new_chat = {
          chat_title: title,
          session_id: s_id,
          isUpload: true,
        };
        let o_historyList = historyList;
        o_historyList.today?.shift();
        o_historyList.today?.unshift(new_chat);
        setHistoryList(o_historyList);
      }
      setSessionId(s_id);

      if (!regenerate) setUploadPrePrompt(currentuploadState.question);
      let ans = {
        ...ans1,
        answers: result,
        isLoading: false,
        source: srcObj,
        msg_id: "",
        rating: 0,
      };

      scrollToBottom();

      // let tempState = [...uploadState, { ...ans }];
      // setUploadState(tempState);
      ans = {
        ...currentuploadState,
        question: "",
      };
      setCurrentuploadState(ans);
      setActiveState(3);
      setStepCompleted(3);
    } catch (error) {
      let ans = {
        ...currentuploadState,
        isLoading: false,
      };
      setCurrentuploadState(ans);
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

      if (actState) {
        let o_historyList = historyList;
        o_historyList.today?.shift();
        setHistoryList(o_historyList);
      }
    }
  };

  /*
  - Function to reset the state values for new session
  - Author - Vinay K M
  - Updated by - Vinay K M
  */
  const startNew = () => {
    setState([]);
    setIsChat(false);
    setSessionId("");
    setUploadStatus(0);
    setActiveState(0);
    setStepCompleted(0);
    setSelectedFiles([]);
    setUploadState([]);
    setChatTitle("New Chat");
    if(defaultUser_bu) setUser_bu(defaultUser_bu);
  };

  const [anchorEl, setAnchorEl] = React.useState(null);
  const open = Boolean(anchorEl);

  const handleClick = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };
  
  const handleDocList = (bu, isShow) => {
    setUser_bu(bu);
    if(isShow) {
      setBuSelected(bu);
      setIsGetDocs(!isGetDocs);
      setOpenDocList(true);
    }
    setAnchorEl(null);
  }
  
  return (
    <Box
      sx={{
        backgroundSize: "cover",
        padding: "0",
      }}
    >
     {Object.keys(state).length > 0 && (<div className="chat-title">
        <h6 className="m-0">
          <span>
          {chatTitle? chatTitle : "New Chat"}
          </span>
          {user_bu && <span className="float-right" style={{
            fontSize: "14px"
          }}>
            Collection: <span className="chat-bu-name" onClick={() => handleDocList(user_bu, true)}>{user_bu}</span>
          </span>}
          </h6>
      </div>)}
     {Object.keys(uploadState).length > 0 && (<div className="chat-title">
        <h6 className="m-0">
          <span>
          {chatTitle? chatTitle : "New Chat"}
          </span>
          {/* {user_bu && <span className="float-right" style={{
            fontSize: "14px"
          }}>
            Collection: <span className="chat-bu-name" onClick={() => handleDocList(user_bu, true)}>{user_bu}</span>
          </span>} */}
          </h6>
      </div>)}
      <Grid
        container
        sx={{
          height: { height: sectionHeight },
          overflow: "auto",
          overflowX: "hidden",
        }}
        className="page-scroller"
        ref={sectionRef}
        style={{ padding: "0px 24px" }}
      >
        <Grid item sm={12}>
          <Container
            maxWidth="xl"
            sx={{ height: `calc(100vh - ${appBarHeight * 4}px)` }}
          >
            <>
              {activeState >= 1 && (
                <UploadProgress
                  activeState={activeState}
                  setActiveState={setActiveState}
                  stepCompleted={stepCompleted}
                />
              )}

              {/* load the upload section if no prompt in that session */}
              {Object.keys(state).length === 0 && activeState <= 1 && (
                <UploadDoc
                  activeState={activeState}
                  setActiveState={setActiveState}
                  stepCompleted={stepCompleted}
                  setStepCompleted={setStepCompleted}
                  selectedFiles={selectedFiles}
                  setSelectedFiles={setSelectedFiles}
                  uploadSessionId={uploadSessionId}
                  setUploadSessionId={setUploadSessionId}
                  currentState={currentState}
                  setCurrentState={setCurrentState}
                />
              )}

              {activeState > 0 && (
                <FilePrompt
                  activeState={activeState}
                  setActiveState={setActiveState}
                  stepCompleted={stepCompleted}
                  setStepCompleted={setStepCompleted}
                  files={selectedFiles}
                  setSelectedFiles={setSelectedFiles}
                  session_id={uploadSessionId}
                  currentuploadState={currentuploadState}
                  setCurrentuploadState={setCurrentuploadState}
                  uploadState={uploadState}
                  setUploadState={setUploadState}
                  uploadStatus={uploadStatus}
                  setUploadStatus={setUploadStatus}
                  makeApiRequest={makeApiRequest}
                  makeFileApiRequest={makeFileApiRequest}
                  scrollToBottom={scrollToBottom}
                  messagesContainerRef={messagesContainerRef}
                  isAutoScroll={isAutoScroll}
                  scrollDirection={scrollDirection}
                  chatTitle={chatTitle}
                  setChatTitle={setChatTitle}
                />
              )}
              {Object.keys(state).length > 0 && (
                <div className="btn-new-prompt">
                  <Button variant="outlined" onClick={startNew}>
                    <AddIcon /> Start a New Prompt
                  </Button>
                </div>
              )}
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
                          // maxWidth: "80%",
                          marginLeft: "auto",
                        }}
                      >
                        <Grid container style={{ justifyContent: "start" }}>
                          <Grid item sm={10.25}>
                            {index === Object.keys(state).length - 1 && (
                              <div ref={messagesContainerRef}>
                                <UserChatMessage
                                  message={qa.question}
                                  readOnly={false}
                                />
                              </div>
                            )}
                            {index !== Object.keys(state).length - 1 && (
                              <UserChatMessage
                                message={qa.question}
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
                          maxWidth: "90%",
                          display: "flex",
                          minWidth: "500px",
                        }}
                        className="answer-font"
                      >
                        {qa.answers && (
                          <Box>
                            {qa.msg_id === "" && <AnswerStreaming
                              answer={qa.answers}
                            />}
                            {qa.msg_id !== "" && <Answer
                              regenerate={
                                state.length - 1 === index ? true : false
                              }
                              answer={qa.answers}
                              sources={qa.source ? qa.source : []}
                              msg_id={qa.msg_id}
                              rating={(qa.rating || qa.rating === 0) ? qa.rating : ""}
                              isFeedback={true}
                              updateState={updateState}
                              makeApiRequest={makeApiRequest}
                              makeApiRequestStreaming={makeApiRequestStreaming}
                              image_details={qa.image_details}
                              get_only_images={qa.get_only_images}
                            />}
                            <span ref={answerBelow}></span>
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
            </>
          </Container>
        </Grid>
      </Grid>
      <Container maxWidth="xl" sm={12} className="first" style={{ padding: "0px 24px" }}>
        {Object.keys(state).length === 0 && activeState === 0 && (
          <>
            <Box display="flex" alignItems="center" justifyContent="center" width="100%" style={{position: "relative"}} >
            <span className="prompt-devider">Or prompt Amgen's internal data collections</span>
              <div className="collection-dropdown">
                <div>
                  <span style={{ color: "#444", fontSize: "16px", fontWeight: 500}}>Collection: </span><Button
                    aria-controls={open ? 'simple-menu' : undefined}
                    aria-haspopup="true"
                    onClick={handleClick}
                    endIcon={<ArrowDropDownIcon />}
                    variant="contained"
                    color="primary"
                    style={{
                      borderRadius: "8px"
                    }}
                  >
                    {user_bu}
                  </Button>
                  <Menu
                    id="simple-menu"
                    anchorEl={anchorEl}
                    open={open}
                    onClose={handleClose}
                    anchorOrigin={{
                      vertical: 'bottom',
                      horizontal: 'right',
                    }}
                    transformOrigin={{
                      vertical: 'top',
                      horizontal: 'center',
                    }}
                    PaperProps={{
                      style: {
                        transform: 'translateY(-155px)',
                      },
                    }}
                  >
                    <span style={{ color: "#444", fontSize: "16px", fontWeight: 500, padding: "5px 15px"}}>Select a Collection</span>
                    {buList?.map((item) => (
                      <MenuItem key={item} onClick={() =>handleDocList(item, false)}>
                        {item}
                        <IconButton onClick={() =>handleDocList(item, true)}>
                          <FolderOpenIcon />
                        </IconButton>
                      </MenuItem>
                    ))}
                  </Menu>
                </div>
              </div>
            </Box>
          </>
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
          alignItems="center"
          spacing={2}
          sx={{ position: "sticky", bottom: 0 }}
        >
          {activeState === 0 && (
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
                  placeholder="Ask me anything from the collection"
                  className="custom-placeholder"
                  style={{
                    borderRadius: "100px",
                    marginTop: activeState === 0 ? "28px" : "5px",
                    border: "1px solid #E0E0E0",
                  }}
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          className="btn-send"
                          disabled={
                            currentState.isLoading ||
                            currentState.question === ""
                          }
                          style={{
                            background: "#fff !important"
                          }}
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
                        There are many ways to write a prompt – from simply
                        asking a question, to requesting Companion to generate
                        content using a new format (lists, bullets, etc.) For
                        best results provide specific and clear instructions in
                        your prompt. To see a list of well-written
                        prompts,&nbsp;
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
          )}

          {activeState === 1 && (
            <>
              {/* <Grid
                item
                sm={12}
                md={12}
                sx={{ pt: "0 !important" }}
                className="text-center"
              >
                <Button
                  variant="contained"
                  size="large"
                  className="btn-rounded"
                  style={{ textTransform: "capitalize" }}
                  onClick={createQuery}
                >
                  Create A Query &nbsp;
                </Button>
              </Grid> */}
              {activeState === 0 && (
                <p className="text-center mt-2 prompt-footer">
                  <span className="text-muted">
                    How does Companion use your documents?
                  </span>
                  <BootstrapTooltip
                    title={
                      <React.Fragment>
                        <span color="inherit">
                          Companion can use your documents to create summaries,
                          generate new content, identify themes, or answer your
                          questions. Documents that you upload will only be
                          accessible by you, for the query you are currently
                          creating. &nbsp;
                        </span>
                        <span
                          className="learn-more"
                          onClick={() => navigate("/faq")}
                        >
                          Learn more
                        </span>
                      </React.Fragment>
                    }
                  >
                    <span>
                      <InfoOutlinedIcon className="text-primary" />
                    </span>
                  </BootstrapTooltip>
                </p>
              )}
            </>
          )}

          {/* {(activeState === 2 || activeState === 3) && ( */}
          {activeState > 0 && (
            <>
              <Grid item sm={12} md={12} sx={{ pt: "0px !important" }}>
                <TextField
                  multiline
                  fullWidth
                  size="medium"
                  value={currentuploadState.question}
                  onKeyDown={(ev) => {
                    if (ev.key === "Enter" && !ev.shiftKey) {
                      ev.preventDefault();
                      makeFileApiRequest(false);
                    }
                  }}
                  disabled={currentuploadState.isLoading}
                  onChange={handleFileQuestionChange}
                  sx={{ background: "#fff", border: "none" }}
                  placeholder={uploadPlaceholder}
                  className="custom-placeholder"
                  style={{
                    borderRadius: "100px",
                    marginTop: "25px",
                    border: "1px solid #E0E0E0",
                  }}
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          disabled={
                            currentuploadState.isLoading ||
                            currentuploadState.question === ""
                          }
                        >
                          <SendIcon
                            className="text-primary"
                            onClick={() => makeFileApiRequest(false)}
                          />
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>
              <p className="text-center mt-1 mb-0">
                <span className="text-muted">
                  What kinds of prompts can I enter?
                </span>
                <BootstrapTooltip
                  title={
                    <React.Fragment>
                      <span color="inherit">
                        There are many ways to write a prompt – from simply
                        asking a question, to requesting Companion to generate
                        content using a new format (lists, bullets, etc.) For
                        best results provide specific and clear instructions in
                        your prompt. To see a list of well-written
                        prompts,&nbsp;
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
          )}
        </Grid>
      </Container>
    </Box>
  );
};

export default UserPrompt;
