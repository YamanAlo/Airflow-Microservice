import React, { useEffect, useState } from 'react';
import axios from 'axios';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

interface SalesSummary {
  product_id: number;
  total_quantity: number;
  total_sale_amount: number;
}

interface SalesMetrics {
  total_items_sold: number;
  total_revenue: number;
  total_products: number;
}

function App() {
  const [salesSummary, setSalesSummary] = useState<SalesSummary[]>([]);
  const [salesMetrics, setSalesMetrics] = useState<SalesMetrics | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [summaryRes, metricsRes] = await Promise.all([
          axios.get('http://localhost:5000/api/sales/summary'),
          axios.get('http://localhost:5000/api/sales/metrics')
        ]);

        setSalesSummary(summaryRes.data.data);
        setSalesMetrics(metricsRes.data.data);
      } catch (error) {
        console.error('Error fetching data:', error);
      }
    };

    fetchData();
  }, []);

  const chartData = {
    labels: salesSummary.map(item => `Product ${item.product_id}`),
    datasets: [
      {
        label: 'Sales Amount ($)',
        data: salesSummary.map(item => item.total_sale_amount),
        backgroundColor: 'rgba(53, 162, 235, 0.5)',
      },
      {
        label: 'Quantity Sold',
        data: salesSummary.map(item => item.total_quantity),
        backgroundColor: 'rgba(75, 192, 192, 0.5)',
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'Sales Summary by Product',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  };

  return (
    <div className="min-h-screen bg-gray-100 py-6 flex flex-col justify-center sm:py-12">
      <div className="relative py-3 sm:max-w-xl md:max-w-4xl mx-auto">
        <div className="relative px-4 py-10 bg-white shadow-lg sm:rounded-3xl sm:p-20">
          <div className="max-w-4xl mx-auto">
            <div className="divide-y divide-gray-200">
              <div className="py-8 text-base leading-6 space-y-4 text-gray-700 sm:text-lg sm:leading-7">
                <h1 className="text-3xl font-bold text-center mb-8">Retail Sales Dashboard</h1>
                
                {/* Metrics Cards */}
                {salesMetrics && (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                    <div className="bg-blue-100 p-4 rounded-lg">
                      <h3 className="text-lg font-semibold">Total Revenue</h3>
                      <p className="text-2xl font-bold">${salesMetrics.total_revenue.toFixed(2)}</p>
                    </div>
                    <div className="bg-green-100 p-4 rounded-lg">
                      <h3 className="text-lg font-semibold">Items Sold</h3>
                      <p className="text-2xl font-bold">{salesMetrics.total_items_sold}</p>
                    </div>
                    <div className="bg-purple-100 p-4 rounded-lg">
                      <h3 className="text-lg font-semibold">Total Products</h3>
                      <p className="text-2xl font-bold">{salesMetrics.total_products}</p>
                    </div>
                  </div>
                )}

                {/* Sales Chart */}
                <div className="mt-8">
                  <Bar options={chartOptions} data={chartData} />
                </div>

                {/* Sales Table */}
                <div className="mt-8">
                  <h2 className="text-xl font-semibold mb-4">Detailed Sales Summary</h2>
                  <div className="overflow-x-auto">
                    <table className="min-w-full table-auto">
                      <thead>
                        <tr className="bg-gray-200">
                          <th className="px-4 py-2">Product ID</th>
                          <th className="px-4 py-2">Quantity Sold</th>
                          <th className="px-4 py-2">Total Sales</th>
                        </tr>
                      </thead>
                      <tbody>
                        {salesSummary.map((item) => (
                          <tr key={item.product_id} className="border-b">
                            <td className="px-4 py-2 text-center">{item.product_id}</td>
                            <td className="px-4 py-2 text-center">{item.total_quantity}</td>
                            <td className="px-4 py-2 text-center">${item.total_sale_amount.toFixed(2)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App; 