import { animated, useSpring } from "@react-spring/web";
import { Card, CardContent, Stack, Typography } from "@mui/material";
import CheckCircleOutlineOutlinedIcon from "@mui/icons-material/CheckCircleOutlineOutlined";

export const SummaryProgress = () => {
  const animatedStyles = useSpring({
    from: { opacity: 0 },
    to: { opacity: 1 },
  });

  return (
    <Stack direction="column" spacing={1}>
      <animated.div
        style={{ ...animatedStyles, width: "50%", marginLeft: "25%" }}
        className="loading-width animate__animated animate__fadeInUp text-center"
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
            <Typography className="mt-1 text-primary">
              <h6>Generating a summary of your documents to include:</h6>
              <p>
                <CheckCircleOutlineOutlinedIcon
                  className="text-primary"
                  style={{ fontSize: "15px" }}
                />{" "}
                Summary of each document
              </p>
            </Typography>
          </CardContent>
        </Card>
      </animated.div>
    </Stack>
  );
};
