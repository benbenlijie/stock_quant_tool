// 主布局组件

import React, { useState } from 'react';
import {
  Layout,
  Menu,
  Button,
  theme,
  Breadcrumb,
  Space,
  Badge,
  Tooltip,
  Typography
} from 'antd';
import {
  DashboardOutlined,
  LineChartOutlined,
  SettingOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  ReloadOutlined,
  BellOutlined
} from '@ant-design/icons';
import { useLocation, useNavigate } from 'react-router-dom';
import { formatDateTime } from '../../utils';

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

interface MainLayoutProps {
  children: React.ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  // 菜单配置
  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: '仪表盘',
    },
    {
      key: '/backtest',
      icon: <LineChartOutlined />,
      label: '历史回测',
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: '参数设置',
    },
  ];

  // 面包屑配置
  const getBreadcrumbItems = () => {
    const pathMap: Record<string, string> = {
      '/': '仪表盘',
      '/backtest': '历史回测',
      '/settings': '参数设置',
    };

    return [
      { title: '首页' },
      { title: pathMap[location.pathname] || '未知页面' }
    ];
  };

  const handleMenuClick = (key: string) => {
    navigate(key);
  };

  const handleRefresh = () => {
    window.location.reload();
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider trigger={null} collapsible collapsed={collapsed}>
        <div className="demo-logo-vertical" style={{
          height: 32,
          margin: 16,
          background: 'rgba(255, 255, 255, 0.2)',
          borderRadius: 6,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
          fontWeight: 'bold'
        }}>
          {collapsed ? 'A股' : 'A股量化选股'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => handleMenuClick(key)}
        />
      </Sider>
      <Layout>
        <Header style={{
          padding: 0,
          background: colorBgContainer,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          paddingRight: 24
        }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed(!collapsed)}
              style={{
                fontSize: '16px',
                width: 64,
                height: 64,
              }}
            />
            <Breadcrumb items={getBreadcrumbItems()} />
          </div>
          
          <Space size="middle">
            <Text type="secondary" style={{ fontSize: '12px' }}>
              更新时间: {formatDateTime(new Date())}
            </Text>
            <Tooltip title="刷新页面">
              <Button
                type="text"
                icon={<ReloadOutlined />}
                onClick={handleRefresh}
              />
            </Tooltip>
            <Badge count={0}>
              <Button
                type="text"
                icon={<BellOutlined />}
                style={{ fontSize: '16px' }}
              />
            </Badge>
          </Space>
        </Header>
        <Content
          style={{
            margin: '24px 16px',
            padding: 24,
            minHeight: 280,
            background: colorBgContainer,
            borderRadius: borderRadiusLG,
          }}
        >
          {children}
        </Content>
      </Layout>
    </Layout>
  );
};

export default MainLayout;