import axios from "axios";
export const api = axios.create();

export const load = (url, config) => api.get(url, config);

export const post = (url, data, config) => api.post(url, data, config);

export const remove = (url, config) => api.delete(url, config);

export const getAllChats = async () => {
  const { data } = (await load) + "/chat";
  return data;
};

export const createNewChat = async () => {
  const { data } = (await post)("/chat", {});
  return data;
};

export const renameChat = async (data) => {
  if (!data.id) return Promise.resolve({ success: false, data: undefined });
  return post(`/chat/${data.id}`, { name: data.name });
};

export const deleteChat = async (data) => {
  if (!data.id) return Promise.resolve({ success: false, data: undefined });
  return remove(`/chat/${data.id}`);
};

export const getChatById = async (id) => {
  if (!id) return Promise.resolve({ success: false, data: undefined });
  const { data } = (await load)`chat/${id}`;
  return data;
};

export async function chatApi(options, signal) {
  const { data } = (await post)(`/chat/message`, {
    signal,
    question: options.question,
  });

  return data;
}

export const rateMessage = async (data) => {
  if (!data.id || !data.chatId)
    return Promise.resolve({ success: false, data: undefined });
  const response = (await post)(`/chat/${data.chatId}/message/${data.id}`, {
    rating: data.rating,
    rating_tag: data.rating_tag,
    rating_comment: data.rating_comment,
  });

  return response.data;
};

export function getCitationFilePath(citation) {
  return `/content/${citation}`;
}
