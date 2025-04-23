import { DatasetsResponse } from "@/types/api.types";
import { getRequest, postRequest } from "./api";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

// GET: Fetch datasets
export const fetchDatasets = async (): Promise<DatasetsResponse> => {
  const response = getRequest("/datasets");
  console.log("response: ", response);
  return response;
};

// hook
export const useFetchDatasets = () => {
  return useQuery<DatasetsResponse>({
    queryKey: ["datasets"], // Unique key for the query
    queryFn: fetchDatasets, // Function that returns data
    // Error handling can be done in the queryFn or globally via QueryClient
  });
};

// POST: Upload file
export const uploadFile = async (
  file: File
): Promise<{ id: string; filename: string }> => {
  const formData = new FormData();
  formData.append("file", file);

  return postRequest("/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};

export const useUploadFile = () => {
  return useMutation({
    mutationFn: uploadFile,
    onSuccess: (data) => {
      // Handle success side effects, if any
      console.log("File uploaded successfully:", data);
    },
    onError: (error: unknown) => {
      // Handle error side effects, if any
      console.error("Error uploading file:", error);
    },
  });
};

// POST: Analyze prompt
export const analyzePrompt = async (payload: {
  prompt: string;
  dataset_id: string;
  chat_history: { role: string; content: string }[];
}): Promise<{ result?: any; job_id: string }> => {
  return postRequest("/analyze", payload);
};

// POST: Chat stream (for streaming explanation)
export const startChat = async (payload: {
  prompt: string;
  chat_history: { role: string; content: string }[];
  job_id: string;
}): Promise<Response> => {
  const response = await fetch("http://localhost:8000/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Chat failed: ${response.statusText}`);
  }

  return response;
};
