// ImageCarousel.js
import React, { useEffect, useState } from 'react';
import { IconButton, Box, Grid, Stack } from '@mui/material';
import ArrowForwardOutlinedIcon from '@mui/icons-material/ArrowForwardOutlined';
import ArrowBackOutlinedIcon from '@mui/icons-material/ArrowBackOutlined';
import { styled } from '@mui/system';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import ThumbUpOffAltIcon from '@mui/icons-material/ThumbUpOffAlt';
import ThumbUpAltIcon from '@mui/icons-material/ThumbUpAlt';
import ThumbDownOffAltIcon from '@mui/icons-material/ThumbDownOffAlt';
import ThumbDownAlt from "@mui/icons-material/ThumbDownAlt";
import DescriptionOutlinedIcon from '@mui/icons-material/DescriptionOutlined';
import { api } from '../../services/api';
import axios from 'axios';

const CarouselContainer = styled(Box)(({ theme }) => ({
    position: 'relative',
    width: '100%',
    maxWidth: '800px',
    margin: '0 auto',
    overflow: 'hidden',
}));

const NavigationButton = styled(IconButton)(({ theme }) => ({
    position: 'absolute',
    top: '40%',
    transform: 'translateY(-50%)',
    zIndex: 1,
    color: "#ccc",
    backgroundColor: "transparent",
    '&:hover': {
        color: "#000",
    },
}));

const PrevButton = styled(NavigationButton)({
    left: 0,
});

const NextButton = styled(NavigationButton)({
    right: 0,
});

const Carousel = ({ images, currentIndex, setCurrentIndex, msg_id }) => {

    const [rating, setRating] = useState(0);
    const [feedbackMessage, setFeedbackMessage] = useState("");

    useEffect(() => {
        setRating(images[currentIndex].rating ? images[currentIndex].rating : 0);
        setFeedbackMessage("");
    }, [currentIndex]);

    const handlePrev = () => {
        setCurrentIndex((prevIndex) => (prevIndex === 0 ? images.length - 1 : prevIndex - 1));
    };

    const handleNext = () => {
        setCurrentIndex((prevIndex) => (prevIndex === images.length - 1 ? 0 : prevIndex + 1));
    };

    let currentData = images[currentIndex];
    const handleFeedbackTags = async (like, value) => {
        if (like === "like") {
            if (value === 0 || value === -1) {
                currentData.rating = 1;
            } else {
                currentData.rating = 0;
            }
        } else {
            if (value === -1) {
                currentData.rating = 0;
            } else {
                currentData.rating = -1;
            }
        }

        let requestData = {
            msg_id: msg_id,
            rating: currentData.rating,
            img_id: currentData.img_id,
        }
        try {
            let url = `${process.env.REACT_APP_API_URL}feedback/image`;
            await api.put(url, requestData);
            setFeedbackMessage("Thank you for your feedback!");
        } catch (error) {
            if (axios.isAxiosError(error)) {
                // Axios-specific error handling
                console.error("Axios Error:", error.message);
                console.error("Response Data:", error.response?.data);
            } else {
                // General error handling
                console.error("Error:", error.message);
            }
        }
        setRating(currentData.rating);
    }
    return (
        <CarouselContainer>
            {currentIndex !== 0 && <PrevButton onClick={handlePrev}>
                <ArrowBackOutlinedIcon />
            </PrevButton>}
            {currentIndex < (images.length - 1) && <NextButton onClick={handleNext}>
                <ArrowForwardOutlinedIcon />
            </NextButton>}
            <Grid container spacing={2} >
                <>
                    <Grid sm={12}>
                        <div style={{
                            paddingLeft: "15px"
                        }} className="mt-1">

                            <h6 className="m-0" style={{
                                fontSize: "16px",
                                margin: "0px 0px",
                                fontWeight: "600"
                            }}>{currentData.title}
                                <span className="text-right f-primary mr-2" style={{
                                    float: "inline-end",
                                    marginTop: "5px"
                                }}>
                                    <a href={currentData.document_url + '#page=' + currentData.page_number} target="_blank" rel="noopener noreferrer" style={{
                                        position: "relative"
                                    }}> View in Document <OpenInNewIcon style={{
                                        position: "absolute",
                                        fontSize: "15px",
                                        top: "2px"
                                    }} /></a></span></h6>

                            <p className="mt-1">
                                <h6 className="m-0" style={{
                                    fontSize: "14px",
                                    margin: "0px 0px",
                                    display: "flex",
                                    fontWeight: "600"
                                }}>
                                    <DescriptionOutlinedIcon style={{
                                        fontSize: "20px",
                                        marginRight: "5px"
                                    }} />{currentData.document_name}
                                </h6>
                            </p>
                        </div>
                    </Grid>
                    <Grid sm={12} item >
                        <div style={{
                            position: "relative",
                            height: '425px',
                            overflowX: 'scroll'
                        }}>
                            <div style={{
                                textAlign: "center"
                            }}>

                                <img alt='data url' src={currentData.url} style={{
                                        maxWidth: "75%",
                                        height: "auto"
                                }} />
                            </div>
                            <p className="mt-1" style={{
                                display: "block"
                            }}>
                                <span className="text-center d-none" style={{
                                    width: "80px",
                                    borderRadius: "100px",
                                    background: "#dde5ed",
                                    padding: "3px 10px"
                                }}>{currentData?.source}</span>
                            </p>
                            <figcaption className="image-caption-modal"><span className='bold'>Caption: </span>{currentData.caption}</figcaption>
                            <div>
                                {feedbackMessage === "" && <Stack spacing={2} direction="row" style={{ background: "transparent" }}>
                                    <>
                                        <span className="btn btn-img-rating" style={{ position: "relative", margin: "10px 10px 0px 0px" }}>
                                            <span style={{
                                                borderRight: "1px solid #444",
                                                paddingRight: "15px"
                                            }}>
                                                Is this image relevant?
                                            </span>
                                            <span
                                            >
                                                <button style={{ border: "none", background: "transparent", padding: "0px 0px 0px 20px", color: "#444", minWidth: "55px", position: "relative" }}>
                                                    {rating === -1 && <>
                                                        <ThumbUpOffAltIcon className="font-20 cursor-pointer icon-left" onClick={() => handleFeedbackTags("like", rating)} />
                                                        <ThumbDownAlt className="font-20 cursor-pointer icon-right" onClick={() => handleFeedbackTags("dislike", rating)} />
                                                    </>
                                                    }
                                                    {rating === 0 && <>
                                                        <ThumbUpOffAltIcon className="font-20 cursor-pointer icon-left" onClick={() => handleFeedbackTags("like", rating)} />
                                                        <ThumbDownOffAltIcon className="font-20 cursor-pointer icon-right" onClick={() => handleFeedbackTags("dislike", rating)} />
                                                    </>
                                                    }
                                                    {rating === 1 && <>
                                                        <ThumbUpAltIcon className="font-20 cursor-pointer icon-left" onClick={() => handleFeedbackTags("like", rating)} />
                                                        <ThumbDownOffAltIcon className="font-20 cursor-pointer icon-right" onClick={() => handleFeedbackTags("dislike", rating)} />
                                                    </>
                                                    }
                                                </button>

                                            </span>
                                        </span>
                                    </>
                                </Stack>}
                                {feedbackMessage !== "" && <>
                                    <Grid className="d-flex bg-white feedback-card mt-2">
                                    <p className="m-0">{feedbackMessage}</p>
                                    </Grid>
                                </>}
                            </div>
                        </div>
                    </Grid>
                </>
            </Grid>
        </CarouselContainer>
    );
};

export default Carousel;
