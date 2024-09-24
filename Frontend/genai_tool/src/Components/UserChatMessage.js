import {
  Avatar,
  Box,
  Card,
  CardContent,
  Stack,
  Typography,
} from "@mui/material";
// import { alpha } from "@mui/material/styles";
import { Person } from "@mui/icons-material";

export const UserChatMessage = ({ message, readOnly = false }) => {
  const initials = localStorage.getItem("email").split("")[0] +
  localStorage.getItem("email").split("")[1];
  return (
    <>
      <Box
        sx={{
          display: message ? "flex" : "none",
          justifyContent: "flex-start",
          mb: 1,
          // maxWidth: "60%",
          marginLeft: "auto",
        }}
        className="user-message-component animate__animated animate__fadeInUp"
      >
        <Stack direction="row" spacing={1}>
        <Avatar style={{ textTransform: "uppercase", fontSize: "85%", marginTop: "13px", borderRadius: "5px" , width: "32px", height: "32px",background: "#586f85" }}>
            {readOnly ? <Person /> : initials}
          </Avatar>
          <Card
            variant="elevation"
            sx={{
              // background: (theme) => alpha("#444", 0.8),
              borderRadius: 3,
              // color: "#fff",
              boxShadow: "none"
            }}
          >
            <CardContent
              sx={{ pb: (theme) => `${theme.spacing(2)} !important` }}
            >
              <Typography variant="body2" style={{
                fontSize: "16px"
              }}>{message}</Typography>
            </CardContent>
          </Card>
        </Stack>
      </Box>
    </>
  );
};
