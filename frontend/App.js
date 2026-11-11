import React, { useState } from 'react';
import {
  StyleSheet,
  Text,
  View,
  SafeAreaView,
  TouchableOpacity,
  useWindowDimensions
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { CartProvider, useCart } from './src/context/CartContext';
import { SystemConfigProvider, useSystemConfig } from './src/context/SystemConfigContext';
import MenuScreen from './src/screens/MenuScreen';
import ReservationScreen from './src/screens/ReservationScreen';
import CartScreen from './src/screens/CartScreen';
import ReservationLookupScreen from './src/screens/ReservationLookupScreen';

function MainApp() {
  const [currentTab, setCurrentTab] = useState('menu');
  const { totalCount } = useCart();
  const { config, refreshConfig } = useSystemConfig();
  const { width } = useWindowDimensions();
  const isWebWide = width > 768;

  const getAnnouncementStyle = (type) => {
    switch (type) {
      case 'danger':
        return { bg: '#f8d7da', border: '#f5c2c7', text: '#842029' };
      case 'warning':
        return { bg: '#fff3cd', border: '#ffecb5', text: '#664d03' };
      default:
        return { bg: '#cff4fc', border: '#b6effb', text: '#055160' };
    }
  };

  const renderScreen = () => {
    if (config.store_status === 'MAINTENANCE') {
      return (
        <View style={styles.maintenanceContainer}>
          <Text style={styles.maintenanceIcon}>🛠️</Text>
          <Text style={styles.maintenanceTitle}>系統維護中</Text>
          <Text style={styles.maintenanceDesc}>
            餐廳目前正在進行系統維護與調整，暫停線上預約及點餐功能。請稍後再試。
          </Text>
          {config.announcement_text ? (
            <View style={styles.maintNoticeBox}>
              <Text style={styles.maintNoticeText}>公告：{config.announcement_text}</Text>
            </View>
          ) : null}
          <TouchableOpacity style={styles.retryBtn} onPress={refreshConfig}>
            <Text style={styles.retryBtnText}>🔄 重新檢查系統狀態</Text>
          </TouchableOpacity>
        </View>
      );
    }

    switch (currentTab) {
      case 'menu':
        return <MenuScreen onNavigateToCart={() => setCurrentTab('cart')} />;
      case 'reservation':
        return <ReservationScreen onBookingSuccess={() => {}} />;
      case 'cart':
        return <CartScreen onNavigateToReservation={() => setCurrentTab('reservation')} />;
      case 'lookup':
        return <ReservationLookupScreen />;
      default:
        return <MenuScreen onNavigateToCart={() => setCurrentTab('cart')} />;
    }
  };

  const annStyle = getAnnouncementStyle(config.announcement_type);

  return (
    <SafeAreaView style={styles.outerContainer}>
      <StatusBar style="dark" />
      <View style={[styles.container, isWebWide && styles.webContainer]}>
        {/* Top Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>餐廳預約與點餐系統</Text>
          <Text style={styles.headerSubtitle}>
            營業時間 {config.opening_time} ~ {config.closing_time} ‧{' '}
            {config.store_status === 'OPEN' ? '🟢 營業中' : config.store_status === 'CLOSED' ? '🟡 休息中' : '🔴 維護中'}
          </Text>
        </View>

        {/* Backend Controlled Closed Banner */}
        {config.store_status === 'CLOSED' && (
          <View style={styles.closedBanner}>
            <Text style={styles.closedBannerText}>
              🌙 本店目前休息中／非營業時段，暫停新預約與線上點餐
            </Text>
          </View>
        )}

        {/* Backend Controlled Announcement Banner */}
        {config.store_status !== 'MAINTENANCE' && config.announcement_text ? (
          <View style={[styles.annBanner, { backgroundColor: annStyle.bg, borderBottomColor: annStyle.border }]}>
            <Text style={[styles.annText, { color: annStyle.text }]}>
              📢 {config.announcement_text}
            </Text>
          </View>
        ) : null}

        {/* Screen Body */}
        <View style={styles.body}>
          {renderScreen()}
        </View>

        {/* Bottom Navigation Bar (Pure Customer Tabs - Admin Removed) */}
        <View style={styles.tabBar}>
          <TouchableOpacity
            style={[styles.tabItem, currentTab === 'menu' && styles.tabItemActive]}
            onPress={() => setCurrentTab('menu')}
          >
            <Text style={styles.tabIcon}>🍽️</Text>
            <Text style={[styles.tabText, currentTab === 'menu' && styles.tabTextActive]}>
              美味菜單
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.tabItem, currentTab === 'reservation' && styles.tabItemActive]}
            onPress={() => setCurrentTab('reservation')}
          >
            <Text style={styles.tabIcon}>📅</Text>
            <Text style={[styles.tabText, currentTab === 'reservation' && styles.tabTextActive]}>
              線上預約
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.tabItem, currentTab === 'cart' && styles.tabItemActive]}
            onPress={() => setCurrentTab('cart')}
          >
            <View style={styles.cartIconWrapper}>
              <Text style={styles.tabIcon}>🛒</Text>
              {totalCount > 0 && (
                <View style={styles.badge}>
                  <Text style={styles.badgeText}>{totalCount > 99 ? '99+' : totalCount}</Text>
                </View>
              )}
            </View>
            <Text style={[styles.tabText, currentTab === 'cart' && styles.tabTextActive]}>
              購物車
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.tabItem, currentTab === 'lookup' && styles.tabItemActive]}
            onPress={() => setCurrentTab('lookup')}
          >
            <Text style={styles.tabIcon}>🔍</Text>
            <Text style={[styles.tabText, currentTab === 'lookup' && styles.tabTextActive]}>
              查詢預約
            </Text>
          </TouchableOpacity>
        </View>
      </View>
    </SafeAreaView>
  );
}

export default function App() {
  return (
    <SystemConfigProvider>
      <CartProvider>
        <MainApp />
      </CartProvider>
    </SystemConfigProvider>
  );
}

const styles = StyleSheet.create({
  outerContainer: {
    flex: 1,
    backgroundColor: '#f1f3f5',
    alignItems: 'center',
    justifyContent: 'center',
  },
  container: {
    flex: 1,
    width: '100%',
    backgroundColor: '#ffffff',
  },
  webContainer: {
    maxWidth: 640,
    width: '100%',
    shadowColor: '#000',
    shadowOpacity: 0.1,
    shadowRadius: 15,
    shadowOffset: { width: 0, height: 4 },
    elevation: 8,
  },
  header: {
    paddingVertical: 14,
    paddingHorizontal: 20,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#f1f3f5',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1d3557',
  },
  headerSubtitle: {
    fontSize: 13,
    color: '#6c757d',
    marginTop: 2,
  },
  closedBanner: {
    backgroundColor: '#fff3cd',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#ffecb5',
  },
  closedBannerText: {
    color: '#664d03',
    fontSize: 13,
    fontWeight: '700',
    textAlign: 'center',
  },
  annBanner: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
  },
  annText: {
    fontSize: 13,
    fontWeight: '600',
    textAlign: 'center',
  },
  body: {
    flex: 1,
  },
  maintenanceContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 28,
    backgroundColor: '#f8f9fa',
  },
  maintenanceIcon: {
    fontSize: 56,
    marginBottom: 14,
  },
  maintenanceTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#1d3557',
    marginBottom: 8,
  },
  maintenanceDesc: {
    fontSize: 14,
    color: '#495057',
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 16,
  },
  maintNoticeBox: {
    backgroundColor: '#fff3cd',
    padding: 12,
    borderRadius: 8,
    marginBottom: 18,
    width: '100%',
  },
  maintNoticeText: {
    color: '#664d03',
    fontSize: 13,
    textAlign: 'center',
    fontWeight: '600',
  },
  retryBtn: {
    backgroundColor: '#1d3557',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
  },
  retryBtnText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  tabBar: {
    flexDirection: 'row',
    height: 62,
    backgroundColor: '#ffffff',
    borderTopWidth: 1,
    borderTopColor: '#dee2e6',
    alignItems: 'center',
    justifyContent: 'space-around',
  },
  tabItem: {
    alignItems: 'center',
    justifyContent: 'center',
    flex: 1,
  },
  tabItemActive: {
    opacity: 1,
  },
  tabIcon: {
    fontSize: 20,
    marginBottom: 2,
  },
  tabText: {
    fontSize: 12,
    color: '#6c757d',
    fontWeight: '500',
  },
  tabTextActive: {
    color: '#e63946',
    fontWeight: 'bold',
  },
  cartIconWrapper: {
    position: 'relative',
  },
  badge: {
    position: 'absolute',
    top: -4,
    right: -12,
    backgroundColor: '#e63946',
    borderRadius: 9,
    minWidth: 18,
    height: 18,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 4,
  },
  badgeText: {
    color: '#ffffff',
    fontSize: 10,
    fontWeight: 'bold',
  },
});
