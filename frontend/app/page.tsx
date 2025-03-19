"use client";
import ChatComponent from "@/components/Chat";
import Chat from "@/components/Chat";

import React, { useState } from "react";

const page = () => {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4">
      <h2 className="text-2xl font-bold mb-4 text-center">
        Chat with DataPrompt
      </h2>
      <ChatComponent />
    </div>
  );
};

export default page;
