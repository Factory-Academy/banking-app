import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from '@/components/Layout';
import { HeldTransactions } from '@/pages/HeldTransactions';
import { AllTransactions } from '@/pages/AllTransactions';
import { EscalatedTransactions } from '@/pages/EscalatedTransactions';
import { ReviewedTransactions } from '@/pages/ReviewedTransactions';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Navigate to="/held" replace />} />
            <Route path="/held" element={<HeldTransactions />} />
            <Route path="/all" element={<AllTransactions />} />
            <Route path="/escalated" element={<EscalatedTransactions />} />
            <Route path="/reviewed" element={<ReviewedTransactions />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
