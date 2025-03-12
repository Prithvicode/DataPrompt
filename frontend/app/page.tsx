"use client";
import ChatComponent from "@/components/Chat";
import Chat from "@/components/Chat";

import React, { useState } from "react";

const page = () => {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4">
      <ChatComponent />
    </div>
  );
};

export default page;
