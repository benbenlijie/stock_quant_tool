// 路由配置

import React from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import MainLayout from '../components/Layout';
import Dashboard from '../pages/Dashboard';
import Backtest from '../pages/Backtest';
import Settings from '../pages/Settings';

const router = createBrowserRouter([
  {
    path: '/',
    element: <MainLayout><Dashboard /></MainLayout>,
  },
  {
    path: '/backtest',
    element: <MainLayout><Backtest /></MainLayout>,
  },
  {
    path: '/settings',
    element: <MainLayout><Settings /></MainLayout>,
  },
  {
    path: '*',
    element: <Navigate to="/" replace />,
  },
]);

export default router;