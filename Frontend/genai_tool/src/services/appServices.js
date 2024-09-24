// apiService.js
import axios from "axios";

const API_BASE_URL = `${process.env.REACT_APP_API_URL}`;

const apiService = async (endpoint, method = "GET", data = null) => {
  const url = `${API_BASE_URL}${endpoint}`;

  try {
    const response = await axios({
      method,
      url,
      // headers: {
      //   "Content-Type": "application/json",
      //   // Add any additional headers here
      // },
      data: data ? data : null,
    });
    return response.data;
  } catch (error) {
    console.error("API Error:", error);
    throw error;
  }
};

export default apiService;
