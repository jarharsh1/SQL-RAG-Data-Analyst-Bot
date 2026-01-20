import React, { useState } from 'react';
import { Database, MessageSquare, Send, Loader2, ChevronDown, ChevronUp } from 'lucide-react';
import QueryInput from './components/QueryInput';
import ResponseCard from './components/ResponseCard';
import { queryAnalyst } from './services/api';
import { QueryResponse } from './types';
import './App.css';

function App() {
  const [messages, setMessages] = useState<Array<{ question: string; response?: QueryResponse; loading?: boolean; error?: string }>>([]);
  const [isQuerying, setIsQuerying] = useState(false);

  const handleQuery = async (question: string) => {
    const newMessage = { question, loading: true };
    setMessages((prev) => [...prev, newMessage]);
    setIsQuerying(true);

    try {
      const response = await queryAnalyst(question, 'web-user');
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = { question, response };
        return updated;
      });
    } catch (error: any) {
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          question,
          error: error.message || 'Failed to get response from analyst'
        };
        return updated;
      });
    } finally {
      setIsQuerying(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Header */}
      <header className="bg-slate-900/50 backdrop-blur-sm border-b border-purple-500/20 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="bg-gradient-to-r from-purple-500 to-pink-500 p-2 rounded-lg">
                <Database className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">SQL + RAG Analyst</h1>
                <p className="text-sm text-gray-400">Ask questions about your data in natural language</p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-sm text-gray-400">Connected</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        {/* Welcome Message */}
        {messages.length === 0 && (
          <div className="text-center py-16">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full mb-6">
              <MessageSquare className="h-8 w-8 text-white" />
            </div>
            <h2 className="text-3xl font-bold text-white mb-4">
              Welcome to your AI Data Analyst
            </h2>
            <p className="text-gray-400 mb-8 max-w-2xl mx-auto">
              Ask me anything about your data. I'll retrieve the right metric definitions,
              generate safe SQL queries, and provide transparent answers with full citations.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-4xl mx-auto">
              <ExampleCard
                question="What was revenue by region last quarter?"
                onClick={handleQuery}
              />
              <ExampleCard
                question="Show me top 10 products by sales"
                onClick={handleQuery}
              />
              <ExampleCard
                question="How many new customers did we acquire last month?"
                onClick={handleQuery}
              />
            </div>
          </div>
        )}

        {/* Messages */}
        <div className="space-y-6 mb-6">
          {messages.map((msg, idx) => (
            <div key={idx} className="space-y-4">
              {/* User Question */}
              <div className="flex justify-end">
                <div className="bg-gradient-to-r from-purple-600 to-pink-600 text-white px-6 py-3 rounded-2xl rounded-tr-none max-w-3xl">
                  <p className="text-sm font-medium">{msg.question}</p>
                </div>
              </div>

              {/* Response */}
              {msg.loading && (
                <div className="flex items-center space-x-3 text-gray-400">
                  <Loader2 className="h-5 w-5 animate-spin" />
                  <span>Analyzing your question...</span>
                </div>
              )}

              {msg.error && (
                <div className="bg-red-900/20 border border-red-500/50 text-red-300 px-6 py-4 rounded-lg">
                  <p className="font-semibold mb-1">Error</p>
                  <p className="text-sm">{msg.error}</p>
                </div>
              )}

              {msg.response && <ResponseCard response={msg.response} />}
            </div>
          ))}
        </div>

        {/* Query Input - Fixed at bottom */}
        <div className="sticky bottom-4">
          <QueryInput onSubmit={handleQuery} disabled={isQuerying} />
        </div>
      </main>
    </div>
  );
}

interface ExampleCardProps {
  question: string;
  onClick: (question: string) => void;
}

function ExampleCard({ question, onClick }: ExampleCardProps) {
  return (
    <button
      onClick={() => onClick(question)}
      className="bg-slate-800/50 hover:bg-slate-800 border border-purple-500/20 hover:border-purple-500/50 rounded-lg p-4 text-left transition-all duration-200 group"
    >
      <div className="flex items-start space-x-2">
        <MessageSquare className="h-5 w-5 text-purple-400 flex-shrink-0 mt-0.5" />
        <p className="text-sm text-gray-300 group-hover:text-white transition-colors">
          {question}
        </p>
      </div>
    </button>
  );
}

export default App;
