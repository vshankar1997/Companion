import { Box, LinearProgress } from "@mui/material";
import React from "react";

function LinearProgressWithLabel(props) {
  return (
    <Box sx={{ display: "flex", alignItems: "center" }}>
      <Box sx={{ width: "100%", mr: 1 }}>
        <LinearProgress variant="determinate" {...props} />
      </Box>
      {/* <Box sx={{ minWidth: 35 }}>
        <Typography variant="body2" color="text.secondary">{`${Math.round(
          props.value
        )}%`}</Typography>
      </Box> */}
    </Box>
  );
}

export default function LinearWithValueLabel(props) {
  const uploadCount = props.secToUpload; //1,00,000
  const [progress, setProgress] = React.useState(10);

  React.useEffect(() => {
    // let progressVal = progress;
    const timer = setInterval(() => {
      // setProgress((prevProgress) => {
      //   // getProgressVal(prevProgress);
      //   prevProgress + 10;
      // });
      if (progress < 100) {
        setProgress((prevProgress) =>
          getProgressVal(prevProgress, props.filesUploaded)
        );
      }
    }, uploadCount);
    return () => {
      clearInterval(timer);
    };
  }, []);

  const getProgressVal = (preVal, isUpload) => {
    let progressVal = progress;
    if (isUpload) {
      progressVal = 100;
    } else if (preVal >= 80 && preVal <= 90) {
      progressVal = preVal + 5;
    } else if (preVal > 90 && preVal < 99) {
      progressVal = preVal + 1;
    } else if (preVal === 99) {
      progressVal = 99;
    } else {
      progressVal = preVal + 10;
    }
    return parseInt(progressVal);
  };

  return (
    <Box sx={{ width: "100%" }}>
      <LinearProgressWithLabel value={progress} />
    </Box>
  );
}
