import React, { useRef } from "react";
import {
  Card,
  CardContent,
  Stack,
  styled,
} from "@mui/material";
// import SmartToyOutlinedIcon from "@mui/icons-material/SmartToyOutlined";
import Tooltip, { tooltipClasses } from "@mui/material/Tooltip";
import { marked } from "marked";
import BlinkingDots from "./BlinkingDots";
import answerIcon from "../../assets/images/Avatar.png"

export const AnswerStreaming = ({
  answer
}) => {

  // console.log("answer", answer)
  // tooltip component
styled(({ className, ...props }) => (
    <Tooltip placement="top" {...props} arrow classes={{ popper: className }} />
  ))(({ theme }) => ({
    [`& .${tooltipClasses.arrow}`]: {
      color: theme.palette.common.black,
    },
    [`& .${tooltipClasses.tooltip}`]: {
      backgroundColor: theme.palette.common.black,
    },
  }));

  const htmlContentRef = useRef(null);
  const renderData = () => {
    let answerObj = marked.parse(answer);
    return (
      <>
      <span dangerouslySetInnerHTML={{__html: answerObj}}></span>
      <span style={{marginBottom: "15px !important"}}><BlinkingDots count={1} /></span>
      </>
    );
  };

  return (
    <Stack
      direction="row"
      spacing={1}
      className="animate__animated animate__fadeInUp answer-wrapper"
    >
      <div>
        {/* <SmartToyOutlinedIcon /> */}
        <img src={answerIcon} width="32px" height="32px" alt="answer icon" />
      </div>
      <Card
        variant="elevation"
        style={{ background: "transparent", boxShadow: "none" }}
      >
        <CardContent
          sx={{
            pb: (theme) => `${theme.spacing(2)} !important`,
            background: "rgb(249, 249, 249)",
            borderRadius: 2,
            boxShadow: "0px 2px 1px -1px rgba(0,0,0,0.2), 0px 1px 1px 0px rgba(0,0,0,0.14), 0px 1px 3px 0px rgba(0,0,0,0.12)"
          }}
          id="copyableCard"
          className="copyableCard answer-border"
          ref={htmlContentRef}
        >
          <span>{renderData()}</span>
          {/* <BlinkingDots count={1} /> */}
        </CardContent>
      </Card>
    </Stack>
  );
};
