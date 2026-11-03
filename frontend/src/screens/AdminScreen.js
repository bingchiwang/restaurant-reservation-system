import React, { useState, useEffect } from 'react';
import {
  StyleSheet,
  Text,
  View,
  ScrollView,
  TextInput,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  FlatList
} from 'react-native';
import { AuthAPI, AdminAPI } from '../api/client';

export default function AdminScreen() {
  const [token, setToken] = useState(null);
  const [email, setEmail] = useState('admin@restaurant.com');
  const [password, setPassword] = useState('admin123');
  const [loggingIn, setLoggingIn] = useState(false);

  // Tab: 'reservations' | 'orders'
  const [activeTab, setActiveTab] = useState('reservations');
  const [selectedDate, setSelectedDate] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [loadingData, setLoadingData] = useState(false);

  const [reservations, setReservations] = useState([]);
  const [orders, setOrders] = useState([]);

  const handleLogin = async () => {
    if (!email || !password) {
      Alert.alert('請輸入帳號密碼', '請填寫管理員信箱與密碼');
      return;
    }
    setLoggingIn(true);
    try {
      const res = await AuthAPI.login(email.trim(), password);
      if (res.success && res.data.token) {
        setToken(res.data.token);
      }
    } catch (err) {
      Alert.alert('登入失敗', err.message || '帳號或密碼錯誤');
    } finally {
      setLoggingIn(false);
    }
  };

  const handleLogout = () => {
    setToken(null);
    setReservations([]);
    setOrders([]);
  };

  useEffect(() => {
    if (token) {
      if (activeTab === 'reservations') {
        fetchReservations();
      } else {
        fetchOrders();
      }
    }
  }, [token, activeTab, selectedDate, statusFilter]);

  const fetchReservations = async () => {
    setLoadingData(true);
    try {
      const res = await AdminAPI.getReservations(
        token,
        selectedDate.trim() || null,
        statusFilter || null
      );
      if (res.success) {
        setReservations(res.data);
      }
    } catch (err) {
      Alert.alert('取得預約失敗', err.message);
    } finally {
      setLoadingData(false);
    }
  };

  const fetchOrders = async () => {
    setLoadingData(true);
    try {
      const res = await AdminAPI.getOrders(
        token,
        selectedDate.trim() || null,
        statusFilter || null
      );
      if (res.success) {
        setOrders(res.data);
      }
    } catch (err) {
      Alert.alert('取得訂單失敗', err.message);
    } finally {
      setLoadingData(false);
    }
  };

  const handleUpdateReservationStatus = (reservationId, newStatus) => {
    const actionLabel = newStatus === 'CANCELLED' ? '取消' : '變更狀態為 ' + newStatus;
    Alert.alert('確認操作', `確定要將此預約${actionLabel}嗎？`, [
      { text: '取消', style: 'cancel' },
      {
        text: '確定',
        style: newStatus === 'CANCELLED' ? 'destructive' : 'default',
        onPress: async () => {
          try {
            await AdminAPI.updateReservationStatus(token, reservationId, newStatus);
            fetchReservations();
          } catch (err) {
            Alert.alert('操作失敗', err.message);
          }
        }
      }
    ]);
  };

  const handleUpdateOrderStatus = (orderId, newStatus) => {
    const actionLabel = newStatus === 'CANCELLED' ? '取消訂單' : `變更為 ${newStatus}`;
    Alert.alert('確認操作', `確定要將訂單 #${orderId} ${actionLabel} 嗎？`, [
      { text: '返回', style: 'cancel' },
      {
        text: '確定',
        style: newStatus === 'CANCELLED' ? 'destructive' : 'default',
        onPress: async () => {
          try {
            await AdminAPI.updateOrderStatus(token, orderId, newStatus);
            fetchOrders();
          } catch (err) {
            Alert.alert('狀態更新失敗', err.message);
          }
        }
      }
    ]);
  };

  if (!token) {
    return (
      <View style={styles.loginContainer}>
        <View style={styles.loginCard}>
          <Text style={styles.loginTitle}>餐廳管理員登入</Text>
          <Text style={styles.loginSubtitle}>請使用管理權限帳號登入後台</Text>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>管理員信箱</Text>
            <TextInput
              style={styles.input}
              value={email}
              onChangeText={setEmail}
              placeholder="admin@restaurant.com"
              keyboardType="email-address"
              autoCapitalize="none"
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>密碼</Text>
            <TextInput
              style={styles.input}
              value={password}
              onChangeText={setPassword}
              placeholder="預設密碼 admin123"
              secureTextEntry
            />
          </View>

          <TouchableOpacity
            style={[styles.loginBtn, loggingIn && styles.disabledBtn]}
            onPress={handleLogin}
            disabled={loggingIn}
          >
            {loggingIn ? (
              <ActivityIndicator color="#ffffff" />
            ) : (
              <Text style={styles.loginBtnText}>登入管理後台</Text>
            )}
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  const renderReservationItem = ({ item }) => (
    <View style={styles.recordCard}>
      <View style={styles.cardHeader}>
        <Text style={styles.codeText}>{item.reservation_code}</Text>
        <View style={[styles.badge, getStatusBadgeStyle(item.status)]}>
          <Text style={styles.badgeText}>{item.status}</Text>
        </View>
      </View>

      <Text style={styles.detailText}>👤 顧客姓名：{item.guest_name || '會員訂位'}</Text>
      <Text style={styles.detailText}>📞 聯絡電話：{item.guest_phone || '無'}</Text>
      <Text style={styles.detailText}>📅 用餐日期：{item.start_at}</Text>
      <Text style={styles.detailText}>👥 人數桌位：{item.party_size} 位 / {item.table_name || `桌號 #${item.table_id}`}</Text>

      <View style={styles.actionRow}>
        {item.status === 'CONFIRMED' && (
          <>
            <TouchableOpacity
              style={[styles.btn, styles.successBtn]}
              onPress={() => handleUpdateReservationStatus(item.reservation_id, 'COMPLETED')}
            >
              <Text style={styles.btnText}>標記完成</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.btn, styles.dangerBtn]}
              onPress={() => handleUpdateReservationStatus(item.reservation_id, 'CANCELLED')}
            >
              <Text style={styles.btnText}>取消預約</Text>
            </TouchableOpacity>
          </>
        )}
      </View>
    </View>
  );

  const renderOrderItem = ({ item }) => (
    <View style={styles.recordCard}>
      <View style={styles.cardHeader}>
        <Text style={styles.codeText}>訂單 #{item.order_id} ({item.order_type === 'PRE_ORDER' ? '預約預點' : '現場點餐'})</Text>
        <View style={[styles.badge, getStatusBadgeStyle(item.status)]}>
          <Text style={styles.badgeText}>{item.status}</Text>
        </View>
      </View>

      <Text style={styles.detailText}>🪑 桌號：{item.table_name || (item.table_id ? `#${item.table_id}` : '未指定')}</Text>
      <Text style={styles.detailText}>🕒 下單時間：{item.created_at}</Text>
      <Text style={styles.priceHighlight}>💰 總金額：NT$ {item.total_amount}</Text>

      {item.items && item.items.length > 0 && (
        <View style={styles.itemList}>
          <Text style={styles.itemTitle}>訂單明細：</Text>
          {item.items.map(it => (
            <Text key={it.order_item_id} style={styles.itemSubText}>
              • {it.item_name_snapshot} x {it.quantity} (NT$ {it.subtotal}){it.note ? ` [備註: ${it.note}]` : ''}
            </Text>
          ))}
        </View>
      )}

      {/* State Machine Transition Actions */}
      <View style={styles.actionRow}>
        {item.status === 'PENDING' && (
          <>
            <TouchableOpacity
              style={[styles.btn, styles.primaryBtn]}
              onPress={() => handleUpdateOrderStatus(item.order_id, 'CONFIRMED')}
            >
              <Text style={styles.btnText}>確認接單</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.btn, styles.dangerBtn]}
              onPress={() => handleUpdateOrderStatus(item.order_id, 'CANCELLED')}
            >
              <Text style={styles.btnText}>取消訂單</Text>
            </TouchableOpacity>
          </>
        )}

        {item.status === 'CONFIRMED' && (
          <>
            <TouchableOpacity
              style={[styles.btn, styles.primaryBtn]}
              onPress={() => handleUpdateOrderStatus(item.order_id, 'PREPARING')}
            >
              <Text style={styles.btnText}>開始製作</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.btn, styles.dangerBtn]}
              onPress={() => handleUpdateOrderStatus(item.order_id, 'CANCELLED')}
            >
              <Text style={styles.btnText}>取消訂單</Text>
            </TouchableOpacity>
          </>
        )}

        {item.status === 'PREPARING' && (
          <TouchableOpacity
            style={[styles.btn, styles.primaryBtn]}
            onPress={() => handleUpdateOrderStatus(item.order_id, 'READY')}
          >
            <Text style={styles.btnText}>餐點完成 (可出餐)</Text>
          </TouchableOpacity>
        )}

        {item.status === 'READY' && (
          <TouchableOpacity
            style={[styles.btn, styles.successBtn]}
            onPress={() => handleUpdateOrderStatus(item.order_id, 'COMPLETED')}
          >
            <Text style={styles.btnText}>完成訂單 (結案)</Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );

  return (
    <View style={styles.container}>
      {/* Top Admin Bar */}
      <View style={styles.adminHeader}>
        <Text style={styles.adminTitle}>餐廳營運管理後台</Text>
        <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout}>
          <Text style={styles.logoutBtnText}>登出</Text>
        </TouchableOpacity>
      </View>

      {/* Switch Tab: Reservations vs Orders */}
      <View style={styles.tabSwitch}>
        <TouchableOpacity
          style={[styles.tabButton, activeTab === 'reservations' && styles.tabButtonActive]}
          onPress={() => setActiveTab('reservations')}
        >
          <Text style={[styles.tabButtonText, activeTab === 'reservations' && styles.tabButtonTextActive]}>
            📅 顧客預約一覽
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tabButton, activeTab === 'orders' && styles.tabButtonActive]}
          onPress={() => setActiveTab('orders')}
        >
          <Text style={[styles.tabButtonText, activeTab === 'orders' && styles.tabButtonTextActive]}>
            🍽️ 顧客點餐訂單
          </Text>
        </TouchableOpacity>
      </View>

      {/* Filter Bar */}
      <View style={styles.filterSection}>
        <TextInput
          style={styles.filterInput}
          placeholder="依日期篩選 (YYYY-MM-DD)"
          value={selectedDate}
          onChangeText={setSelectedDate}
        />
        {selectedDate ? (
          <TouchableOpacity style={styles.clearDateBtn} onPress={() => setSelectedDate('')}>
            <Text style={styles.clearDateText}>✕ 清除</Text>
          </TouchableOpacity>
        ) : null}
      </View>

      {/* List content */}
      {loadingData ? (
        <View style={styles.centerContainer}>
          <ActivityIndicator size="large" color="#1d3557" />
          <Text style={{ marginTop: 8, color: '#6c757d' }}>載入資料中...</Text>
        </View>
      ) : (
        <FlatList
          data={activeTab === 'reservations' ? reservations : orders}
          keyExtractor={(item) => String(activeTab === 'reservations' ? item.reservation_id : item.order_id)}
          renderItem={activeTab === 'reservations' ? renderReservationItem : renderOrderItem}
          contentContainerStyle={styles.listContent}
          ListEmptyComponent={
            <View style={styles.centerContainer}>
              <Text style={styles.emptyText}>查無相符之紀錄</Text>
            </View>
          }
        />
      )}
    </View>
  );
}

function getStatusBadgeStyle(status) {
  switch (status) {
    case 'CONFIRMED':
    case 'READY':
      return { backgroundColor: '#2a9d8f' };
    case 'PREPARING':
      return { backgroundColor: '#e76f51' };
    case 'COMPLETED':
      return { backgroundColor: '#457b9d' };
    case 'CANCELLED':
      return { backgroundColor: '#e63946' };
    default:
      return { backgroundColor: '#f4a261' };
  }
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  loginContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#f1f3f5',
  },
  loginCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 24,
    width: '100%',
    maxWidth: 400,
    shadowColor: '#000',
    shadowOpacity: 0.1,
    shadowRadius: 10,
    elevation: 4,
  },
  loginTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1d3557',
    textAlign: 'center',
  },
  loginSubtitle: {
    fontSize: 13,
    color: '#6c757d',
    textAlign: 'center',
    marginTop: 4,
    marginBottom: 20,
  },
  inputGroup: {
    marginBottom: 14,
  },
  label: {
    fontSize: 13,
    color: '#495057',
    marginBottom: 6,
    fontWeight: '600',
  },
  input: {
    backgroundColor: '#f8f9fa',
    borderWidth: 1,
    borderColor: '#ced4da',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 14,
  },
  loginBtn: {
    backgroundColor: '#1d3557',
    borderRadius: 8,
    paddingVertical: 12,
    alignItems: 'center',
    marginTop: 10,
  },
  loginBtnText: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: 'bold',
  },
  adminHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#dee2e6',
  },
  adminTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1d3557',
  },
  logoutBtn: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    backgroundColor: '#e9ecef',
  },
  logoutBtnText: {
    fontSize: 12,
    color: '#495057',
    fontWeight: '600',
  },
  tabSwitch: {
    flexDirection: 'row',
    backgroundColor: '#e9ecef',
    padding: 4,
    marginHorizontal: 16,
    marginTop: 12,
    borderRadius: 8,
  },
  tabButton: {
    flex: 1,
    paddingVertical: 10,
    alignItems: 'center',
    borderRadius: 6,
  },
  tabButtonActive: {
    backgroundColor: '#ffffff',
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 2,
  },
  tabButtonText: {
    fontSize: 14,
    color: '#6c757d',
    fontWeight: '600',
  },
  tabButtonTextActive: {
    color: '#1d3557',
    fontWeight: 'bold',
  },
  filterSection: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    marginTop: 10,
    marginBottom: 6,
    gap: 8,
  },
  filterInput: {
    flex: 1,
    backgroundColor: '#ffffff',
    borderWidth: 1,
    borderColor: '#ced4da',
    borderRadius: 6,
    paddingHorizontal: 12,
    paddingVertical: 6,
    fontSize: 13,
  },
  clearDateBtn: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    backgroundColor: '#dee2e6',
    borderRadius: 6,
  },
  clearDateText: {
    fontSize: 12,
    color: '#495057',
  },
  listContent: {
    padding: 16,
    paddingBottom: 40,
  },
  recordCard: {
    backgroundColor: '#ffffff',
    borderRadius: 10,
    padding: 14,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#e9ecef',
    shadowColor: '#000',
    shadowOpacity: 0.03,
    shadowRadius: 5,
    elevation: 2,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#f1f3f5',
    paddingBottom: 6,
  },
  codeText: {
    fontSize: 15,
    fontWeight: 'bold',
    color: '#1d3557',
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  badgeText: {
    color: '#ffffff',
    fontSize: 11,
    fontWeight: 'bold',
  },
  detailText: {
    fontSize: 13,
    color: '#495057',
    marginBottom: 4,
  },
  priceHighlight: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#e63946',
    marginTop: 4,
    marginBottom: 6,
  },
  itemList: {
    backgroundColor: '#f8f9fa',
    padding: 8,
    borderRadius: 6,
    marginVertical: 6,
  },
  itemTitle: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#495057',
    marginBottom: 2,
  },
  itemSubText: {
    fontSize: 12,
    color: '#6c757d',
    marginBottom: 2,
  },
  actionRow: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 8,
  },
  btn: {
    flex: 1,
    paddingVertical: 8,
    borderRadius: 6,
    alignItems: 'center',
  },
  primaryBtn: {
    backgroundColor: '#1d3557',
  },
  successBtn: {
    backgroundColor: '#2a9d8f',
  },
  dangerBtn: {
    backgroundColor: '#e63946',
  },
  btnText: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: 'bold',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 40,
  },
  emptyText: {
    fontSize: 14,
    color: '#adb5bd',
  },
  disabledBtn: {
    opacity: 0.6,
  },
});
