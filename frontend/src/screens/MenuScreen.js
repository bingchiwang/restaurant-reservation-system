import React, { useState, useEffect, useCallback } from 'react';
import {
  StyleSheet,
  Text,
  View,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  Alert
} from 'react-native';
import { MenuAPI } from '../api/client';
import { useCart } from '../context/CartContext';
import { useSystemConfig } from '../context/SystemConfigContext';

export default function MenuScreen({ onNavigateToCart }) {
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  const { addItem, totalCount, totalAmount } = useCart();
  const { config } = useSystemConfig();

  const canOrder = config.store_status === 'OPEN' && config.ordering_enabled;

  const loadCategories = useCallback(async () => {
    try {
      const res = await MenuAPI.getCategories();
      if (res.success) {
        setCategories(res.data);
      }
    } catch (err) {
      console.warn("無法取得餐點分類，使用預設值", err);
    }
  }, []);

  const loadMenuItems = useCallback(async (catId, showSpinner = true) => {
    if (showSpinner) setLoading(true);
    try {
      const res = await MenuAPI.getItems(catId);
      if (res.success) {
        setItems(res.data);
      }
    } catch (err) {
      Alert.alert("載入失敗", "無法取得菜單，請確認後端服務已啟動");
    } finally {
      if (showSpinner) setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCategories();
  }, [loadCategories, config.updated_at]);

  useEffect(() => {
    loadMenuItems(selectedCategory, items.length === 0);
  }, [selectedCategory, config.updated_at, loadMenuItems]);

  const handleAddToCart = (item) => {
    if (!canOrder) {
      Alert.alert("暫停點餐", "目前後端管理員已暫停點餐功能");
      return;
    }
    addItem(item);
  };

  const renderCategoryItem = ({ item }) => {
    const isSelected = item.category_id === selectedCategory;
    return (
      <TouchableOpacity
        style={[styles.categoryChip, isSelected && styles.categoryChipActive]}
        onPress={() => setSelectedCategory(item.category_id)}
      >
        <Text style={[styles.categoryText, isSelected && styles.categoryTextActive]}>
          {item.name}
        </Text>
      </TouchableOpacity>
    );
  };

  const renderMenuItem = ({ item }) => {
    return (
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <Text style={styles.itemName}>{item.name}</Text>
          <Text style={styles.itemPrice}>NT$ {item.price}</Text>
        </View>
        {item.description ? (
          <Text style={styles.itemDesc}>{item.description}</Text>
        ) : null}
        <View style={styles.cardFooter}>
          <Text style={styles.categoryBadge}>{item.category_name}</Text>
          <TouchableOpacity
            style={[styles.addButton, !canOrder && styles.addButtonDisabled]}
            onPress={() => handleAddToCart(item)}
            disabled={!canOrder}
          >
            <Text style={styles.addButtonText}>
              {canOrder ? "+ 加入購物車" : "暫停點餐"}
            </Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  };

  return (
    <View style={styles.container}>
      {!canOrder && (
        <View style={styles.pausedBanner}>
          <Text style={styles.pausedBannerText}>
            ⚠️ 目前暫停線上／現場點餐服務，僅供瀏覽菜單
          </Text>
        </View>
      )}

      {/* Category Filter Bar */}
      <View style={styles.filterBar}>
        <TouchableOpacity
          style={[styles.categoryChip, selectedCategory === null && styles.categoryChipActive]}
          onPress={() => setSelectedCategory(null)}
        >
          <Text style={[styles.categoryText, selectedCategory === null && styles.categoryTextActive]}>
            全部
          </Text>
        </TouchableOpacity>
        <FlatList
          horizontal
          showsHorizontalScrollIndicator={false}
          data={categories}
          keyExtractor={(item) => String(item.category_id)}
          renderItem={renderCategoryItem}
        />
      </View>

      {/* Menu Items List */}
      {loading ? (
        <View style={styles.centerContainer}>
          <ActivityIndicator size="large" color="#e63946" />
          <Text style={styles.loadingText}>載入美味餐點中...</Text>
        </View>
      ) : (
        <FlatList
          data={items}
          keyExtractor={(item) => String(item.item_id)}
          renderItem={renderMenuItem}
          contentContainerStyle={styles.listContent}
          ListEmptyComponent={
            <View style={styles.centerContainer}>
              <Text style={styles.emptyText}>目前此分類暫無可供應之餐點</Text>
            </View>
          }
        />
      )}

      {/* Floating Cart Bar */}
      {totalCount > 0 && (
        <TouchableOpacity style={styles.floatingCart} onPress={onNavigateToCart}>
          <View style={styles.cartInfo}>
            <Text style={styles.cartBadge}>{totalCount} 件餐點</Text>
            <Text style={styles.cartTotal}>NT$ {totalAmount.toFixed(0)}</Text>
          </View>
          <Text style={styles.cartCheckoutText}>檢視購物車 ➔</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  pausedBanner: {
    backgroundColor: '#fff3cd',
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderBottomWidth: 1,
    borderBottomColor: '#ffe69c',
  },
  pausedBannerText: {
    color: '#664d03',
    fontSize: 13,
    fontWeight: '600',
    textAlign: 'center',
  },
  filterBar: {
    flexDirection: 'row',
    paddingVertical: 12,
    paddingHorizontal: 16,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e9ecef',
  },
  categoryChip: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#e9ecef',
    marginRight: 8,
  },
  categoryChipActive: {
    backgroundColor: '#e63946',
  },
  categoryText: {
    fontSize: 14,
    color: '#495057',
    fontWeight: '500',
  },
  categoryTextActive: {
    color: '#ffffff',
    fontWeight: 'bold',
  },
  listContent: {
    padding: 16,
    paddingBottom: 90,
  },
  card: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 5,
    shadowOffset: { width: 0, height: 2 },
    elevation: 2,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  itemName: {
    fontSize: 17,
    fontWeight: 'bold',
    color: '#212529',
    flex: 1,
    marginRight: 8,
  },
  itemPrice: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#e63946',
  },
  itemDesc: {
    fontSize: 14,
    color: '#6c757d',
    marginBottom: 12,
    lineHeight: 20,
  },
  cardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 4,
  },
  categoryBadge: {
    fontSize: 12,
    color: '#6c757d',
    backgroundColor: '#f1f3f5',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  addButton: {
    backgroundColor: '#1d3557',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 8,
  },
  addButtonDisabled: {
    backgroundColor: '#adb5bd',
  },
  addButtonText: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: '600',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 40,
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: '#6c757d',
  },
  emptyText: {
    fontSize: 15,
    color: '#adb5bd',
  },
  floatingCart: {
    position: 'absolute',
    bottom: 16,
    left: 16,
    right: 16,
    backgroundColor: '#e63946',
    borderRadius: 14,
    paddingVertical: 14,
    paddingHorizontal: 20,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    shadowColor: '#e63946',
    shadowOpacity: 0.3,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 4 },
    elevation: 6,
  },
  cartInfo: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  cartBadge: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: 'bold',
    marginRight: 12,
  },
  cartTotal: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '800',
  },
  cartCheckoutText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: 'bold',
  },
});
