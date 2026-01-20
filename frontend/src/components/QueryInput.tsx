import React, { useState } from 'react';
import { Send } from 'lucide-react';

interface QueryInputProps {
  onSubmit: (question: string) => void;
  disabled?: boolean;
}

export default function QueryInput({ onSubmit, disabled }: QueryInputProps) {
  const [input, setInput] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !disabled) {
      onSubmit(input.trim());
      setInput('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="bg-slate-800/80 backdrop-blur-sm border border-purple-500/30 rounded-2xl shadow-2xl p-2">
        <div className="flex items-end space-x-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
            placeholder="Ask a question about your data... (e.g., 'What was revenue by region last quarter?')"
            disabled={disabled}
            className="flex-1 bg-transparent text-white placeholder-gray-500 focus:outline-none resize-none px-4 py-3 max-h-32 min-h-[3rem]"
            rows={1}
          />
          <button
            type="submit"
            disabled={disabled || !input.trim()}
            className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 disabled:from-gray-600 disabled:to-gray-600 disabled:cursor-not-allowed text-white p-3 rounded-xl transition-all duration-200 flex-shrink-0"
          >
            <Send className="h-5 w-5" />
          </button>
        </div>
        <div className="flex items-center justify-between px-4 py-2 text-xs text-gray-500">
          <span>Press Enter to send, Shift+Enter for new line</span>
          <span>Powered by RAG + GPT-4</span>
        </div>
      </div>
    </form>
  );
}
