import React, { useState } from 'react';
import {
  StyleSheet,
  Text,
  View,
  FlatList,
  TouchableOpacity,
  TextInput,
  Alert,
  ActivityIndicator
} from 'react-native';
import { useCart } from '../context/CartContext';
import { OrderAPI } from '../api/client';

export default function CartScreen({ onNavigateToReservation }) {
  const { cartItems, updateQuantity, removeItem, clearCart, totalAmount, totalCount } = useCart();
  const [tableNumber, setTableNumber] = useState('');
  const [ordering, setOrdering] = useState(false);
  const [orderConfirmed, setOrderConfirmed] = useState(null);

  const handleDineInOrder = async () => {
    if (!tableNumber.trim()) {
      Alert.alert('請輸入桌號', '請輸入現場桌位編號或掃描桌位 QR Code');
      return;
    }
    const tableId = parseInt(tableNumber.trim(), 10);
    if (isNaN(tableId) || tableId <= 0) {
      Alert.alert('桌號錯誤', '請輸入正確的桌位數字編號');
      return;
    }

    setOrdering(true);
    try {
      const payloadItems = cartItems.map(i => ({
        item_id: i.item_id,
        quantity: i.quantity,
        note: i.note
      }));
      const res = await OrderAPI.createDineInOrder(tableId, payloadItems);
      if (res.success) {
        setOrderConfirmed(res.data);
        clearCart();
      }
    } catch (err) {
      Alert.alert('點餐失敗', err.message || '無法建立現場訂單，請確認桌號是否有效');
    } finally {
      setOrdering(false);
    }
  };

  if (orderConfirmed) {
    return (
      <View style={styles.confirmedContainer}>
        <Text style={styles.confirmedIcon}>✅</Text>
        <Text style={styles.confirmedTitle}>現場點餐送單成功！</Text>
        <Text style={styles.confirmedSubtitle}>廚房已收到訂單並開始排單製作</Text>

        <View style={styles.orderSummaryBox}>
          <Text style={styles.summaryRow}>訂單編號：#{orderConfirmed.order_id}</Text>
          <Text style={styles.summaryRow}>桌號：{orderConfirmed.table_name || `#${orderConfirmed.table_id}`}</Text>
          <Text style={styles.summaryRow}>訂單狀態：{orderConfirmed.status}</Text>
          <Text style={styles.summaryRowBold}>總金額：NT$ {orderConfirmed.total_amount}</Text>
        </View>

        <TouchableOpacity style={styles.backButton} onPress={() => setOrderConfirmed(null)}>
          <Text style={styles.backButtonText}>回到菜單與購物車</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (cartItems.length === 0) {
    return (
      <View style={styles.emptyContainer}>
        <Text style={styles.emptyIcon}>🛒</Text>
        <Text style={styles.emptyTitle}>您的購物車目前是空的</Text>
        <Text style={styles.emptySubtitle}>前往菜單瀏覽並加入想品嚐的美味餐點吧！</Text>
      </View>
    );
  }

  const renderItem = ({ item }) => (
    <View style={styles.cartCard}>
      <View style={styles.itemHeader}>
        <Text style={styles.itemName}>{item.name}</Text>
        <TouchableOpacity onPress={() => removeItem(item.item_id)}>
          <Text style={styles.deleteText}>刪除</Text>
        </TouchableOpacity>
      </View>
      <Text style={styles.unitPrice}>單價：NT$ {item.price}</Text>

      <View style={styles.quantityRow}>
        <View style={styles.counter}>
          <TouchableOpacity style={styles.counterBtn} onPress={() => updateQuantity(item.item_id, -1)}>
            <Text style={styles.counterBtnText}>-</Text>
          </TouchableOpacity>
          <Text style={styles.counterText}>{item.quantity}</Text>
          <TouchableOpacity style={styles.counterBtn} onPress={() => updateQuantity(item.item_id, 1)}>
            <Text style={styles.counterBtnText}>+</Text>
          </TouchableOpacity>
        </View>
        <Text style={styles.subtotal}>小計 NT$ {(item.price * item.quantity).toFixed(0)}</Text>
      </View>
    </View>
  );

  return (
    <View style={styles.container}>
      <FlatList
        data={cartItems}
        keyExtractor={(item) => String(item.item_id)}
        renderItem={renderItem}
        contentContainerStyle={styles.list}
      />

      {/* Cart Summary & Order Actions */}
      <View style={styles.footer}>
        <View style={styles.totalRow}>
          <Text style={styles.totalLabel}>餐點共 {totalCount} 件，合計</Text>
          <Text style={styles.totalAmount}>NT$ {totalAmount.toFixed(0)}</Text>
        </View>

        {/* Option 1: Link with Online Reservation */}
        <TouchableOpacity style={styles.reserveButton} onPress={onNavigateToReservation}>
          <Text style={styles.reserveButtonText}>📅 預約訂位並附帶預點餐</Text>
        </TouchableOpacity>

        {/* Option 2: Dine-in Table Instant Order */}
        <View style={styles.dineInBox}>
          <Text style={styles.dineInLabel}>現場已就坐？輸入桌號即刻送單：</Text>
          <View style={styles.dineInInputRow}>
            <TextInput
              style={styles.tableInput}
              placeholder="桌號 (例: 1)"
              keyboardType="number-pad"
              value={tableNumber}
              onChangeText={setTableNumber}
            />
            <TouchableOpacity
              style={[styles.dineInButton, ordering && styles.disabledBtn]}
              onPress={handleDineInOrder}
              disabled={ordering}
            >
              {ordering ? (
                <ActivityIndicator color="#ffffff" size="small" />
              ) : (
                <Text style={styles.dineInButtonText}>送出現場點餐</Text>
              )}
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  list: {
    padding: 16,
    paddingBottom: 20,
  },
  cartCard: {
    backgroundColor: '#ffffff',
    borderRadius: 10,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#e9ecef',
  },
  itemHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  itemName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#212529',
    flex: 1,
  },
  deleteText: {
    color: '#e63946',
    fontSize: 13,
  },
  unitPrice: {
    fontSize: 13,
    color: '#6c757d',
    marginTop: 2,
    marginBottom: 8,
  },
  quantityRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  counter: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f1f3f5',
    borderRadius: 6,
  },
  counterBtn: {
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  counterBtnText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#495057',
  },
  counterText: {
    paddingHorizontal: 8,
    fontSize: 14,
    fontWeight: 'bold',
    color: '#212529',
  },
  subtotal: {
    fontSize: 15,
    fontWeight: 'bold',
    color: '#1d3557',
  },
  footer: {
    backgroundColor: '#ffffff',
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: '#dee2e6',
  },
  totalRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  totalLabel: {
    fontSize: 14,
    color: '#495057',
  },
  totalAmount: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#e63946',
  },
  reserveButton: {
    backgroundColor: '#1d3557',
    borderRadius: 8,
    paddingVertical: 12,
    alignItems: 'center',
    marginBottom: 12,
  },
  reserveButtonText: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: 'bold',
  },
  dineInBox: {
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    padding: 10,
    borderWidth: 1,
    borderColor: '#e9ecef',
  },
  dineInLabel: {
    fontSize: 12,
    color: '#6c757d',
    marginBottom: 6,
  },
  dineInInputRow: {
    flexDirection: 'row',
    gap: 8,
  },
  tableInput: {
    flex: 1,
    backgroundColor: '#ffffff',
    borderWidth: 1,
    borderColor: '#ced4da',
    borderRadius: 6,
    paddingHorizontal: 10,
    paddingVertical: 6,
    fontSize: 14,
  },
  dineInButton: {
    backgroundColor: '#2a9d8f',
    borderRadius: 6,
    paddingHorizontal: 14,
    justifyContent: 'center',
    alignItems: 'center',
  },
  dineInButtonText: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: 'bold',
  },
  disabledBtn: {
    backgroundColor: '#adb5bd',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#f8f9fa',
  },
  emptyIcon: {
    fontSize: 54,
    marginBottom: 12,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#495057',
    marginBottom: 6,
  },
  emptySubtitle: {
    fontSize: 14,
    color: '#adb5bd',
    textAlign: 'center',
  },
  confirmedContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
    backgroundColor: '#ffffff',
  },
  confirmedIcon: {
    fontSize: 50,
    marginBottom: 12,
  },
  confirmedTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1d3557',
  },
  confirmedSubtitle: {
    fontSize: 14,
    color: '#6c757d',
    marginTop: 4,
    marginBottom: 20,
  },
  orderSummaryBox: {
    backgroundColor: '#f8f9fa',
    padding: 16,
    borderRadius: 10,
    width: '100%',
    marginBottom: 24,
    borderWidth: 1,
    borderColor: '#dee2e6',
  },
  summaryRow: {
    fontSize: 14,
    color: '#495057',
    marginBottom: 6,
  },
  summaryRowBold: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#e63946',
    marginTop: 4,
  },
  backButton: {
    backgroundColor: '#1d3557',
    borderRadius: 8,
    paddingVertical: 12,
    paddingHorizontal: 24,
  },
  backButtonText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: 'bold',
  },
});
