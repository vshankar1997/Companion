import React from 'react';
import '../../assets/styles/answer.css';

const BlinkingDots = ({ count }) => {
    // const dotCount = 1;
    // const dots = Array.from({ length: dotCount }, (_, index) => (
    //     <span key={index} className="dot" style={{ '--delay': index }}>
    //         &nbsp;
    //     </span>
    // ));

    return (
        <span style={{
            position: "relative"
        }}>
            <span className="typing-indicator">
                <span className="data-stream">
                    <span className="dot" style={
                        { '--delay': '1',
                        position: "relative",
                        left: "0px",
                        top: "7px",
                        marginBottom: "15px" }
                        }>
                        &nbsp;
                    </span>
                </span>
            </span>
        </span>
    );
};

export default BlinkingDots;
