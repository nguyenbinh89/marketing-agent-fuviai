"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Trash2, Bot, User } from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

interface Message {
  role: "user" | "assistant";
  content: string;
  ts: number;
}

const SESSION_ID = "dashboard-chat-" + Math.random().toString(36).slice(2, 8);

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Xin chào! Tôi là AI Marketing Agent của FuviAI. Tôi có thể giúp bạn:\n\n- Tư vấn chiến lược marketing cho doanh nghiệp VN\n- Phân tích campaign và đề xuất tối ưu\n- Viết content cho Facebook, TikTok, Zalo, Email\n- Nghiên cứu từ khoá SEO và thị trường\n\nBạn cần hỗ trợ gì hôm nay?",
      ts: Date.now(),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || loading) return;

    setMessages((prev) => [...prev, { role: "user", content: text, ts: Date.now() }]);
    setInput("");
    setLoading(true);

    try {
      const res = await api.chat(SESSION_ID, text);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: res.response, ts: Date.now() },
      ]);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Lỗi không xác định";
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `❌ Lỗi: ${msg}`, ts: Date.now() },
      ]);
    } finally {
      setLoading(false);
      textareaRef.current?.focus();
    }
  };

  const clearChat = async () => {
    await api.clearSession(SESSION_ID).catch(() => {});
    setMessages([{
      role: "assistant",
      content: "Cuộc trò chuyện đã được xoá. Tôi có thể giúp gì cho bạn?",
      ts: Date.now(),
    }]);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const QUICK_PROMPTS = [
    "Tư vấn chiến lược marketing F&B budget 10 triệu/tháng",
    "Viết caption Facebook cho sản phẩm skincare cao cấp",
    "Phân tích xu hướng TMĐT Việt Nam Q2/2027",
    "Gợi ý từ khoá SEO cho landing page phần mềm quản lý",
  ];

  return (
    <div className="flex flex-col h-full max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-xl font-bold text-slate-800">Chat với AI Agent</h1>
          <p className="text-sm text-slate-500">Marketing Expert · Tiếng Việt</p>
        </div>
        <button onClick={clearChat} className="btn-outline flex items-center gap-2 text-sm">
          <Trash2 size={14} />
          Xoá chat
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto scrollbar-thin space-y-4 pb-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={cn("flex gap-3", msg.role === "user" ? "justify-end" : "justify-start")}
          >
            {msg.role === "assistant" && (
              <div className="w-8 h-8 rounded-full bg-brand-500 flex items-center justify-center flex-shrink-0 mt-1">
                <Bot size={16} className="text-white" />
              </div>
            )}
            <div
              className={cn(
                "max-w-[80%] rounded-2xl px-4 py-3 text-sm",
                msg.role === "user"
                  ? "bg-brand-500 text-white rounded-tr-sm"
                  : "bg-white border border-slate-200 text-slate-800 rounded-tl-sm"
              )}
            >
              {msg.role === "assistant" ? (
                <div
                  className="prose-ai"
                  dangerouslySetInnerHTML={{
                    __html: msg.content
                      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
                      .replace(/\n/g, "<br/>"),
                  }}
                />
              ) : (
                msg.content
              )}
            </div>
            {msg.role === "user" && (
              <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center flex-shrink-0 mt-1">
                <User size={16} className="text-slate-600" />
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-brand-500 flex items-center justify-center flex-shrink-0">
              <Bot size={16} className="text-white" />
            </div>
            <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-sm px-4 py-3">
              <div className="flex gap-1.5 items-center h-4">
                {[0, 1, 2].map((i) => (
                  <span
                    key={i}
                    className="w-2 h-2 bg-slate-300 rounded-full animate-bounce"
                    style={{ animationDelay: `${i * 0.15}s` }}
                  />
                ))}
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Quick Prompts */}
      {messages.length <= 1 && (
        <div className="mb-3 flex flex-wrap gap-2">
          {QUICK_PROMPTS.map((p) => (
            <button
              key={p}
              onClick={() => { setInput(p); textareaRef.current?.focus(); }}
              className="text-xs px-3 py-1.5 bg-brand-50 text-brand-600 rounded-full hover:bg-brand-100 transition-colors"
            >
              {p}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="flex gap-3 items-end">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Nhập câu hỏi... (Enter để gửi, Shift+Enter xuống dòng)"
          rows={2}
          className="textarea flex-1"
          disabled={loading}
        />
        <button
          onClick={sendMessage}
          disabled={!input.trim() || loading}
          className="btn-primary flex items-center gap-2 h-10 flex-shrink-0"
        >
          <Send size={15} />
          Gửi
        </button>
      </div>
    </div>
  );
}
