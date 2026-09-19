import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Send, Bot, User, Sparkles, Loader2, AlertCircle, Mic, ArrowRight } from 'lucide-react';
import { queryApi, QueryResultData } from '../api/query';
import { useAuth } from '../context/AuthContext';
import { StatusBadge } from '../components/StatusBadge';
import { EmptyState } from '../components/EmptyState';

interface Message {
  id: string;
  sender: 'USER' | 'ASSISTANT';
  text: string;
  data?: QueryResultData['result'];
  intent?: string;
  timestamp: string;
}

export const QueryAssistant: React.FC = () => {
  const { currentShop } = useAuth();
  const navigate = useNavigate();

  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      sender: 'ASSISTANT',
      text: 'Hello. I can answer questions regarding your stock, today\'s sales, incoming shipments, and pending reviews. How can I help you today?',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sampleQueries = [
    'How much rice is left?',
    'How much rice did we sell today?',
    'What stock arrived today?',
    'Show low stock items',
    'Show pending reviews',
  ];

  const handleSend = async (queryText?: string) => {
    const q = (queryText || input).trim();
    if (!q || !currentShop) return;

    const userMessage: Message = {
      id: String(Date.now()),
      sender: 'USER',
      text: q,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMessage]);
    if (!queryText) setInput('');
    setIsLoading(true);
    setError(null);

    try {
      const res = await queryApi.askQuery(currentShop.id, q);
      if (res.success && res.data) {
        const assistantMessage: Message = {
          id: String(Date.now() + 1),
          sender: 'ASSISTANT',
          text: `Intent recognized: ${res.data.intent}`,
          intent: res.data.intent,
          data: res.data.result,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };
        setMessages((prev) => [...prev, assistantMessage]);
      } else {
        setError(res.error?.message || 'Failed to get answer.');
      }
    } catch (err: unknown) {
      const e = err as { response?: { data?: { error?: { message?: string } } }; message?: string };
      setError(e.response?.data?.error?.message || e.message || 'Error communicating with assistant.');
    } finally {
      setIsLoading(false);
    }
  };

  const renderDataResult = (data?: QueryResultData['result'], intent?: string) => {
    if (!data) return null;

    if (intent === 'CURRENT_STOCK') {
      if (data.product && data.current_stock !== undefined) {
        return (
          <div className="mt-2 p-3 bg-white rounded-lg border border-slate-200 text-xs space-y-1">
            <span className="font-semibold text-slate-900 block">{data.product}</span>
            <div className="text-sm font-bold text-slate-900">
              Current Stock: {data.current_stock} {data.unit || ''}
            </div>
            <div className="text-[11px] text-slate-500">
              Baseline: {data.baseline_quantity ?? '—'} | Inward: +{data.confirmed_in ?? 0} | Outward: -{data.confirmed_out ?? 0}
            </div>
          </div>
        );
      }
      if (Array.isArray(data.inventory)) {
        return (
          <div className="mt-2 p-3 bg-white rounded-lg border border-slate-200 text-xs space-y-2">
            <span className="font-semibold text-slate-900 block">Inventory Overview</span>
            <div className="divide-y divide-slate-100">
              {data.inventory.map((i: any) => (
                <div key={i.product_id} className="py-1.5 flex justify-between">
                  <span className="font-medium text-slate-800">{i.product_name}</span>
                  <span className="font-bold text-slate-900">
                    {i.current_stock !== null ? `${i.current_stock} ${i.default_unit}` : 'No baseline'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        );
      }
    }

    if (intent === 'SALES_TODAY' && Array.isArray(data.sales_today)) {
      return (
        <div className="mt-2 p-3 bg-white rounded-lg border border-slate-200 text-xs space-y-1.5">
          <span className="font-semibold text-slate-900 block">Sales Recorded Today</span>
          {data.sales_today.length === 0 ? (
            <p className="text-slate-500">No confirmed sales statements recorded today.</p>
          ) : (
            <div className="space-y-1">
              {data.sales_today.map((s, idx) => (
                <div key={idx} className="flex justify-between py-1 border-b border-slate-50">
                  <span className="font-medium text-slate-800">{s.product}</span>
                  <span className="font-bold text-slate-900">{s.quantity} {s.unit}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      );
    }

    if (intent === 'RECEIPTS_TODAY' && Array.isArray(data.receipts_today)) {
      return (
        <div className="mt-2 p-3 bg-white rounded-lg border border-slate-200 text-xs space-y-1.5">
          <span className="font-semibold text-slate-900 block">Receipts Recorded Today</span>
          {data.receipts_today.length === 0 ? (
            <p className="text-slate-500">No incoming stock statements recorded today.</p>
          ) : (
            <div className="space-y-1">
              {data.receipts_today.map((r, idx) => (
                <div key={idx} className="flex justify-between py-1 border-b border-slate-50">
                  <span className="font-medium text-slate-800">{r.product}</span>
                  <span className="font-bold text-emerald-700">+{r.quantity} {r.unit}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      );
    }

    if (intent === 'LOW_STOCK' && Array.isArray(data.low_stock_products)) {
      return (
        <div className="mt-2 p-3 bg-white rounded-lg border border-slate-200 text-xs space-y-1.5">
          <span className="font-semibold text-amber-800 block">Items Requiring Reorder</span>
          {data.low_stock_products.length === 0 ? (
            <p className="text-slate-500">All product stock levels are currently healthy.</p>
          ) : (
            <div className="space-y-1">
              {data.low_stock_products.map((p: any) => (
                <div key={p.product_id} className="flex justify-between py-1 border-b border-slate-50">
                  <span className="font-medium text-slate-800">{p.product_name}</span>
                  <span className="font-bold text-amber-600">{p.current_stock} {p.default_unit}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      );
    }

    if (intent === 'REVIEW_QUEUE') {
      return (
        <div className="mt-2 p-3 bg-white rounded-lg border border-slate-200 text-xs">
          <span className="font-semibold text-slate-900 block">Review Queue Status</span>
          <p className="text-slate-700 mt-1">
            Pending Flagged Statements: <strong>{data.pending_reviews ?? 0}</strong>
          </p>
        </div>
      );
    }

    if (data.message) {
      return (
        <p className="mt-2 p-2.5 bg-white rounded-lg border border-slate-200 text-xs text-slate-700">
          {data.message}
        </p>
      );
    }

    return null;
  };

  if (!currentShop) {
    return (
      <EmptyState
        title="No Shop Selected"
        description="Please select an existing shop or create a new shop to use the assistant."
        actionLabel="Create or Select Shop"
        onAction={() => navigate('/shop-setup')}
        icon={Bot}
      />
    );
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto flex flex-col h-[calc(100vh-8rem)]">
      {/* Header */}
      <div className="shrink-0">
        <h1 className="text-xl font-bold text-slate-900">Voice & Natural Language Assistant</h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Ask questions about your shop inventory. All answers are derived directly from the authoritative ledger.
        </p>
      </div>

      {/* Suggested queries */}
      <div className="flex flex-wrap gap-2 shrink-0">
        {sampleQueries.map((q, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(q)}
            className="text-xs px-3 py-1.5 bg-white hover:bg-slate-100 text-slate-700 font-medium rounded-full border border-slate-200 flex items-center space-x-1 transition-colors shadow-2xs"
          >
            <Sparkles className="w-3 h-3 text-indigo-500" />
            <span>{q}</span>
          </button>
        ))}
      </div>

      {/* Chat Messages Container */}
      <div className="flex-1 overflow-y-auto p-4 bg-white rounded-xl border border-slate-200 shadow-xs space-y-4">
        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex items-start space-x-3 ${
              m.sender === 'USER' ? 'flex-row-reverse space-x-reverse' : ''
            }`}
          >
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                m.sender === 'USER'
                  ? 'bg-slate-900 text-white'
                  : 'bg-indigo-600 text-white'
              }`}
            >
              {m.sender === 'USER' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
            </div>

            <div
              className={`max-w-xl rounded-xl p-3.5 text-xs ${
                m.sender === 'USER'
                  ? 'bg-slate-900 text-white'
                  : 'bg-slate-50 border border-slate-100 text-slate-800'
              }`}
            >
              <p className="leading-relaxed font-medium">{m.text}</p>
              {m.intent && (
                <div className="mt-1">
                  <StatusBadge status={m.intent} size="sm" />
                </div>
              )}
              {renderDataResult(m.data, m.intent)}
              <span
                className={`text-[10px] block mt-1.5 ${
                  m.sender === 'USER' ? 'text-slate-400 text-right' : 'text-slate-400'
                }`}
              >
                {m.timestamp}
              </span>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-full bg-indigo-600 text-white flex items-center justify-center shrink-0">
              <Bot className="w-4 h-4" />
            </div>
            <div className="bg-slate-50 border border-slate-100 rounded-xl p-3 text-xs text-slate-500 flex items-center space-x-2">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              <span>Analyzing question and computing ledger totals...</span>
            </div>
          </div>
        )}

        {error && (
          <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-lg flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Input bar */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="flex items-center space-x-2 shrink-0"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question (e.g. 'How much rice did we sell today?')..."
          className="flex-1 px-4 py-3 text-sm bg-white border border-slate-300 rounded-xl focus:outline-hidden focus:ring-2 focus:ring-indigo-500 shadow-xs"
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          className="p-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl shadow-xs disabled:opacity-50 transition-colors"
          title="Send Question"
        >
          <Send className="w-5 h-5" />
        </button>
      </form>
    </div>
  );
};
