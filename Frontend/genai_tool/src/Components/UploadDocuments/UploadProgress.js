import "../KnowledgeBase/KnowledgeBase.css";
import React from "react";
import { Step, StepLabel, Stepper } from "@mui/material";
import { styled } from "@mui/material/styles";
import Check from "@mui/icons-material/Check";
import StepConnector, {
  stepConnectorClasses,
} from "@mui/material/StepConnector";
const UploadProgress = (props) => {
  const steps = ["Upload Documents", "Create A Query", "Generate Response"];
  let stateProp = props;
  const QontoStepIconRoot = styled("div")(({ theme, ownerState }) => ({
    color: "var(--primary-color)",
    display: "flex",
    height: 22,
    alignItems: "center",
    "& .QontoStepIcon-completedIcon": {
      color: "#FFF",
      zIndex: 1,
      fontSize: 18,
      background: "var(--primary-color)",
      borderRadius: "50%",
    },
    "& .QontoStepIcon-circle": {
      width: 8,
      height: 8,
      borderRadius: "50%",
      background: "var(--secondary-color)",
      border: "2px solid currentColor",
      padding: 3,
      opacity: 0.6,
    },
    "& .QontoStepIcon-Completed": {
      width: 8,
      height: 8,
      borderRadius: "50%",
      background: "currentColor",
      border: "2px solid currentColor",
      padding: 3,
      opacity: 1,
    },
  }));

  const QontoConnector = styled(StepConnector)(({ theme }) => ({
    [`&.${stepConnectorClasses.alternativeLabel}`]: {
      top: 10,
      left: "calc(-50% + 16px)",
      right: "calc(50% + 16px)",
    },
    [`&.${stepConnectorClasses.active}`]: {
      [`& .${stepConnectorClasses.line}`]: {
        borderColor: "var(--primary-color)",
      },
    },
    [`&.${stepConnectorClasses.completed}`]: {
      [`& .${stepConnectorClasses.line}`]: {
        borderColor: "var(--primary-color)",
      },
    },
    [`& .${stepConnectorClasses.line}`]: {
      borderColor: "var(--primary-color)",
      borderTopWidth: 1,
      borderRadius: 1,
    },
  }));

  function QontoStepIcon(props) {
    return (
      <QontoStepIconRoot>
        {props < stateProp.stepCompleted ? (
          <Check className="QontoStepIcon-completedIcon" />
        ) : props < stateProp.activeState ? (
          <div className="QontoStepIcon-Completed here" />
        ) : (
          <div className="QontoStepIcon-circle" />
        )}
      </QontoStepIconRoot>
    );
  }
  return (
    <div className="upload-progressbar">
      <Stepper
        alternativeLabel
        activeStep={props?.activeState}
        connector={<QontoConnector active={2} />}
      >
        {steps.map((label, key) => (
          <Step key={label}>
            <StepLabel
              StepIconComponent={() => QontoStepIcon(key)}
              className="progressbar-text"
            >
              <span
                className={
                  key < props.activeState ? "active-step" : "inactive-step"
                }
              >
                {" "}
                {label}{" "}
              </span>
            </StepLabel>
          </Step>
        ))}
      </Stepper>
    </div>
  );
};

export default UploadProgress;
