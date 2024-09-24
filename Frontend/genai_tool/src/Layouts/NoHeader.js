import React from "react";
const NoHeader = ({ children }) => {
  return (
    <div style={{ height: "100%" }}>
      <main style={{ height: "100%" }}>{children}</main>
    </div>
  );
};

export default NoHeader;
