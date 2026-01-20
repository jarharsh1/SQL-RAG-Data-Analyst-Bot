import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Database, Clock, FileText, Download, Copy, Check } from 'lucide-react';
import { QueryResponse } from '../types';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import DataTable from './DataTable';

interface ResponseCardProps {
  response: QueryResponse;
}

export default function ResponseCard({ response }: ResponseCardProps) {
  const [showSQL, setShowSQL] = useState(false);
  const [showTransparency, setShowTransparency] = useState(false);
  const [showData, setShowData] = useState(true);
  const [copied, setCopied] = useState(false);

  const copySQL = () => {
    if (response.transparency?.sql_executed) {
      navigator.clipboard.writeText(response.transparency.sql_executed);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const downloadCSV = () => {
    if (!response.data?.data) return;

    const headers = response.data.columns.join(',');
    const rows = response.data.data.map(row =>
      response.data!.columns.map(col => {
        const value = row[col];
        // Escape quotes and wrap in quotes if contains comma
        const stringValue = String(value ?? '');
        return stringValue.includes(',') ? `"${stringValue.replace(/"/g, '""')}"` : stringValue;
      }).join(',')
    );

    const csv = [headers, ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `query_results_${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-slate-800/50 backdrop-blur-sm border border-purple-500/20 rounded-2xl overflow-hidden">
      {/* Answer */}
      <div className="p-6">
        <div className="flex items-start space-x-3 mb-4">
          <div className="bg-gradient-to-r from-purple-500 to-pink-500 p-2 rounded-lg flex-shrink-0">
            <Database className="h-5 w-5 text-white" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-white mb-2">Answer</h3>
            <p className="text-gray-300 leading-relaxed">{response.answer}</p>
          </div>
        </div>

        {/* Metadata */}
        <div className="flex items-center space-x-6 text-sm text-gray-400 mt-4 pt-4 border-t border-gray-700">
          <div className="flex items-center space-x-2">
            <Clock className="h-4 w-4" />
            <span>{response.metadata.execution_time_ms.toFixed(0)}ms</span>
          </div>
          <div className="flex items-center space-x-2">
            <FileText className="h-4 w-4" />
            <span>{response.metadata.rows_returned} rows</span>
          </div>
          {response.data && response.data.truncated && (
            <div className="text-yellow-400">
              <span>Results truncated</span>
            </div>
          )}
        </div>
      </div>

      {/* Data Table */}
      {response.data && response.data.data && response.data.data.length > 0 && (
        <div className="border-t border-gray-700">
          <button
            onClick={() => setShowData(!showData)}
            className="w-full px-6 py-3 flex items-center justify-between hover:bg-slate-700/30 transition-colors"
          >
            <span className="text-white font-medium">Data Results ({response.data.row_count} rows)</span>
            <div className="flex items-center space-x-2">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  downloadCSV();
                }}
                className="p-2 hover:bg-purple-600/20 rounded-lg transition-colors"
                title="Download CSV"
              >
                <Download className="h-4 w-4 text-purple-400" />
              </button>
              {showData ? <ChevronUp className="h-5 w-5 text-gray-400" /> : <ChevronDown className="h-5 w-5 text-gray-400" />}
            </div>
          </button>
          {showData && (
            <div className="p-6 pt-0">
              <DataTable data={response.data.data} columns={response.data.columns} />
            </div>
          )}
        </div>
      )}

      {/* SQL Query */}
      {response.transparency?.sql_executed && (
        <div className="border-t border-gray-700">
          <button
            onClick={() => setShowSQL(!showSQL)}
            className="w-full px-6 py-3 flex items-center justify-between hover:bg-slate-700/30 transition-colors"
          >
            <span className="text-white font-medium">SQL Query</span>
            <div className="flex items-center space-x-2">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  copySQL();
                }}
                className="p-2 hover:bg-purple-600/20 rounded-lg transition-colors"
                title="Copy SQL"
              >
                {copied ? <Check className="h-4 w-4 text-green-400" /> : <Copy className="h-4 w-4 text-purple-400" />}
              </button>
              {showSQL ? <ChevronUp className="h-5 w-5 text-gray-400" /> : <ChevronDown className="h-5 w-5 text-gray-400" />}
            </div>
          </button>
          {showSQL && (
            <div className="px-6 pb-6">
              <SyntaxHighlighter
                language="sql"
                style={vscDarkPlus}
                customStyle={{
                  margin: 0,
                  borderRadius: '0.5rem',
                  fontSize: '0.875rem',
                }}
              >
                {response.transparency.sql_executed}
              </SyntaxHighlighter>
            </div>
          )}
        </div>
      )}

      {/* Transparency Info */}
      {response.transparency && (
        <div className="border-t border-gray-700">
          <button
            onClick={() => setShowTransparency(!showTransparency)}
            className="w-full px-6 py-3 flex items-center justify-between hover:bg-slate-700/30 transition-colors"
          >
            <span className="text-white font-medium">Transparency & Citations</span>
            {showTransparency ? <ChevronUp className="h-5 w-5 text-gray-400" /> : <ChevronDown className="h-5 w-5 text-gray-400" />}
          </button>
          {showTransparency && (
            <div className="px-6 pb-6 space-y-4">
              {/* Tables Accessed */}
              {response.transparency.tables_accessed && response.transparency.tables_accessed.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-purple-400 mb-2">Tables Accessed</h4>
                  <div className="flex flex-wrap gap-2">
                    {Object.keys(response.transparency.tables_accessed).map((table) => (
                      <span key={table} className="bg-purple-900/30 text-purple-300 px-3 py-1 rounded-full text-sm">
                        {table}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Metric Definitions */}
              {response.transparency.definitions_used && response.transparency.definitions_used.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-purple-400 mb-2">Metric Definitions Used</h4>
                  <div className="space-y-2">
                    {response.transparency.definitions_used.map((def, idx) => (
                      <div key={idx} className="bg-slate-700/30 rounded-lg p-3">
                        <p className="text-white font-medium">{def.name}</p>
                        <p className="text-sm text-gray-400 mt-1">Formula: {def.formula}</p>
                        <p className="text-xs text-gray-500 mt-1">Source: {def.source_table}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Assumptions */}
              {response.transparency.assumptions && response.transparency.assumptions.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-purple-400 mb-2">Assumptions Made</h4>
                  <ul className="space-y-1">
                    {response.transparency.assumptions.map((assumption, idx) => (
                      <li key={idx} className="text-sm text-gray-400 flex items-start space-x-2">
                        <span className="text-purple-400 mt-1">•</span>
                        <span>{assumption}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Citations */}
              {response.transparency.citations && response.transparency.citations.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-purple-400 mb-2">Citations</h4>
                  <div className="space-y-2">
                    {response.transparency.citations.map((citation, idx) => (
                      <div key={idx} className="bg-slate-700/30 rounded-lg p-3">
                        <p className="text-sm text-white">{citation.source}</p>
                        {citation.location && (
                          <p className="text-xs text-gray-500 mt-1">Location: {citation.location}</p>
                        )}
                        <p className="text-xs text-gray-400 mt-1">{citation.content}</p>
                        <p className="text-xs text-purple-400 mt-1">Relevance: {(citation.relevance_score * 100).toFixed(0)}%</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Suggested Actions */}
      {response.suggested_actions && response.suggested_actions.length > 0 && (
        <div className="border-t border-gray-700 p-6">
          <h4 className="text-sm font-semibold text-white mb-3">Suggested Actions</h4>
          <div className="flex flex-wrap gap-2">
            {response.suggested_actions.map((action, idx) => (
              <button
                key={idx}
                className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg text-sm transition-colors"
                onClick={() => {
                  if (action.type === 'export_csv') {
                    downloadCSV();
                  }
                }}
              >
                {action.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
