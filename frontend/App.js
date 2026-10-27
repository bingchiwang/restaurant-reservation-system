import React, { useState } from 'react';
import {
  StyleSheet,
  Text,
  View,
  SafeAreaView,
  TouchableOpacity
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { CartProvider, useCart } from './src/context/CartContext';
import MenuScreen from './src/screens/MenuScreen';
import ReservationScreen from './src/screens/ReservationScreen';
import CartScreen from './src/screens/CartScreen';
import ReservationLookupScreen from './src/screens/ReservationLookupScreen';

function MainApp() {
  const [currentTab, setCurrentTab] = useState('menu');
  const { totalCount } = useCart();

  const renderScreen = () => {
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

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="dark" />
      {/* Top Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>餐廳預約與點餐系統</Text>
        <Text style={styles.headerSubtitle}>優質美味 ‧ 線上即時預約</Text>
      </View>

      {/* Screen Body */}
      <View style={styles.body}>
        {renderScreen()}
      </View>

      {/* Bottom Navigation Bar */}
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
    </SafeAreaView>
  );
}

export default function App() {
  return (
    <CartProvider>
      <MainApp />
    </CartProvider>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  header: {
    paddingVertical: 12,
    paddingHorizontal: 20,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#f1f3f5',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1d3557',
  },
  headerSubtitle: {
    fontSize: 12,
    color: '#6c757d',
    marginTop: 2,
  },
  body: {
    flex: 1,
  },
  tabBar: {
    flexDirection: 'row',
    height: 60,
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
    fontSize: 18,
    marginBottom: 2,
  },
  tabText: {
    fontSize: 11,
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
    right: -10,
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
