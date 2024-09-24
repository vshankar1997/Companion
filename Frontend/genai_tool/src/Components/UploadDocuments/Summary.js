import React from "react";
import {
  Card,
  CardContent,
  Typography,
  Stack,
  Avatar,
  styled,
  // ThemeProvider,
  // Chip,
  // Divider,
  // createTheme,
  // Accordion,
  // AccordionSummary,
  // AccordionDetails,
} from "@mui/material";
// import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import SmartToyOutlinedIcon from "@mui/icons-material/SmartToyOutlined";
import { useSnackbar } from "notistack";
import Tooltip, { tooltipClasses } from "@mui/material/Tooltip";

export const Summary = ({ answer, sources, readonly }) => {
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

  const { enqueueSnackbar } = useSnackbar();
  const handleCopyClick = async (textToCopy) => {
    try {
      await navigator.clipboard.writeText(textToCopy);
      enqueueSnackbar("Copied to clipboard", {
        variant: "success",
        anchorOrigin: {
          vertical: "top",
          horizontal: "right",
        },
      });
    } catch (error) {
      console.error("Error copying to clipboard:", error);
    }
  };

  const answerWithListsString = answer.join("");
  return (
    <Stack
      direction="row"
      spacing={1}
      className="animate__animated animate__fadeInUp"
    >
      <Avatar sx={{ background: (theme) => theme.palette.primary.main }}>
        <SmartToyOutlinedIcon />
      </Avatar>
      <Card
        variant="elevation"
        sx={{
          background: "rgb(249, 249, 249)",
          borderRadius: 2,
        }}
      >
        <CardContent sx={{ pb: (theme) => `${theme.spacing(2)} !important` }}>
          <Typography
            variant="body2"
            sx={{ margin: "1em", whiteSpace: "pre-line" }}
            dangerouslySetInnerHTML={{ __html: answerWithListsString }}
          />
          <button className="btn-copy" onClick={() => handleCopyClick(answer)}>
            <BootstrapTooltip
              title={
                <React.Fragment>
                  <span color="inherit">Copy to clipboard</span>
                </React.Fragment>
              }
            >
              <span>
                <ContentCopyIcon className="font-14" />
                Copy
              </span>
            </BootstrapTooltip>
          </button>
        </CardContent>
      </Card>
    </Stack>
  );
};
