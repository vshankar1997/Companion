import { animated, useSpring } from "@react-spring/web";
import { Card, CardContent, Stack, Typography } from "@mui/material";
import { styled } from "@mui/material/styles";
import CheckCircleOutlineOutlinedIcon from "@mui/icons-material/CheckCircleOutlineOutlined";

/*
  - Function for dot animation while loading the UI for the answer
  - Author - Vinay K M
  - Updated by - Vinay K M
  */
const Keyframes = styled("span")({
  "@keyframes loading": {
    "0%": {
      content: '""',
    },
    "25%": {
      content: '"."',
    },
    "50%": {
      content: '".."',
    },
    "75%": {
      content: '"..."',
    },
    "100%": {
      content: '""',
    },
  },
  "&:after": {
    content: '""',
    animation: "loading 1s infinite ease",
  },
});

export const AnswerLoading = (props) => {
  const animatedStyles = useSpring({
    from: { opacity: 0 },
    to: { opacity: 1 },
  });

  return (
    <Stack direction="row" spacing={1} classNa>
      <animated.div
        style={{ ...animatedStyles }}
        className="loading-width animate__animated animate__fadeInUp"
      >
        <Card
          variant="elevation"
          sx={{
            width: "100%",
            borderRadius: 0,
            border: "none",
            mb: 2,
            background: "transparent",
            boxShadow: "none",
          }}
        >
          <CardContent>
            {/* {props.isSummary && (
              <Typography>
                <CheckCircleOutlineOutlinedIcon
                  className="text-success"
                  style={{ fontSize: "16px" }}
                />{" "}
                Generating summary <Keyframes />
              </Typography>
            )} */}
            <Typography className="mt-1">
              <CheckCircleOutlineOutlinedIcon
                className="text-success"
                style={{ fontSize: "14px" }}
              />{" "}
              Generating results
              <Keyframes />
            </Typography>
          </CardContent>
        </Card>
      </animated.div>
    </Stack>
  );
};
