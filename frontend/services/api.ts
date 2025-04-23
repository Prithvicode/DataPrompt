import axiosInstance from "./axios";
import { AxiosError, type AxiosRequestConfig } from "axios";

// Generic GET request wrapper
export const getRequest = async (url: string, config?: AxiosRequestConfig) => {
  try {
    const response = await axiosInstance.get(url, config);

    return response.data;
  } catch (error) {
    if (error instanceof AxiosError && error.response) {
      throw new Error(
        error.response.data?.message || "An unexpected error occurred."
      );
    }
    // Re-throw the error to be handled by the caller
    throw error;
  }
};
export const postRequest = async (
  url: string,
  data?: any,
  config?: AxiosRequestConfig
) => {
  try {
    const response = await axiosInstance.post(url, data, config);

    return response.data;
  } catch (error) {
    if (error instanceof AxiosError && error.response) {
      throw new Error(
        error.response.data?.message || "An unexpected error occurred."
      );
    }
  }
};
