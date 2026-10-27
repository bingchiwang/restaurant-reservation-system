import React, { createContext, useContext, useState, useMemo } from 'react';

const CartContext = createContext(null);

export function CartProvider({ children }) {
  const [cartItems, setCartItems] = useState([]);

  const addItem = (item) => {
    setCartItems(prev => {
      const existing = prev.find(i => i.item_id === item.item_id);
      if (existing) {
        return prev.map(i =>
          i.item_id === item.item_id ? { ...i, quantity: i.quantity + 1 } : i
        );
      }
      return [...prev, { ...item, quantity: 1, note: '' }];
    });
  };

  const updateQuantity = (itemId, delta) => {
    setCartItems(prev => {
      return prev
        .map(i => {
          if (i.item_id === itemId) {
            const newQty = i.quantity + delta;
            return newQty > 0 ? { ...i, quantity: newQty } : null;
          }
          return i;
        })
        .filter(Boolean);
    });
  };

  const removeItem = (itemId) => {
    setCartItems(prev => prev.filter(i => i.item_id !== itemId));
  };

  const clearCart = () => {
    setCartItems([]);
  };

  const totalAmount = useMemo(() => {
    return cartItems.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  }, [cartItems]);

  const totalCount = useMemo(() => {
    return cartItems.reduce((sum, item) => sum + item.quantity, 0);
  }, [cartItems]);

  return (
    <CartContext.Provider value={{
      cartItems,
      addItem,
      updateQuantity,
      removeItem,
      clearCart,
      totalAmount,
      totalCount
    }}>
      {children}
    </CartContext.Provider>
  );
}

export function useCart() {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error("useCart must be used within a CartProvider");
  }
  return context;
}
