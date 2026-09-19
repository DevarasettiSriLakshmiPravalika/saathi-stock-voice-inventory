import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { Inventory } from '../pages/Inventory';
import { Statements } from '../pages/Statements';
import { inventoryApi } from '../api/inventory';
import { statementsApi } from '../api/statements';
import { productsApi } from '../api/products';
import { AuthProvider } from '../context/AuthContext';

vi.mock('../api/inventory', () => ({
  inventoryApi: {
    getShopInventory: vi.fn(),
    setBaseline: vi.fn(),
    getProductHistory: vi.fn(),
  },
}));

vi.mock('../api/statements', () => ({
  statementsApi: {
    listStatements: vi.fn(),
    getStatement: vi.fn(),
    overrideStatement: vi.fn(),
  },
}));

vi.mock('../api/products', () => ({
  productsApi: {
    listProducts: vi.fn(),
  },
}));

vi.mock('../api/shops', () => ({
  shopsApi: {
    listUserShops: vi.fn().mockResolvedValue({
      success: true,
      data: [
        {
          id: 'shop-123',
          name: 'Demo Shop',
          owner_id: 'user-1',
          role: 'OWNER',
          is_active: true,
          created_at: '2026-09-19T00:00:00Z',
          updated_at: '2026-09-19T00:00:00Z',
        },
      ],
    }),
  },
}));

vi.mock('../api/auth', () => ({
  authApi: {
    getMe: vi.fn().mockResolvedValue({
      success: true,
      data: {
        id: 'user-1',
        name: 'Shop Owner',
        phone: '+919876543210',
        is_active: true,
        is_phone_verified: true,
        created_at: '2026-09-19T00:00:00Z',
        updated_at: '2026-09-19T00:00:00Z',
      },
    }),
  },
}));

describe('Inventory Page Component', () => {
  it('renders inventory items computed from backend calculation', async () => {
    localStorage.setItem('saathi_access_token', 'mock_token');
    localStorage.setItem('saathi_selected_shop_id', 'shop-123');

    vi.mocked(inventoryApi.getShopInventory).mockResolvedValue({
      success: true,
      data: [
        {
          product_id: 'p-1',
          product_name: 'Basmati Rice',
          default_unit: 'bag',
          current_stock: 95.0,
          baseline_quantity: 100.0,
          confirmed_in: 0.0,
          confirmed_out: 5.0,
          unit: 'bag',
          has_baseline: true,
        },
      ],
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <Inventory />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Basmati Rice')).toBeInTheDocument();
      expect(screen.getByText('95')).toBeInTheDocument();
      expect(screen.getByText('100')).toBeInTheDocument();
      expect(screen.getByText('-5')).toBeInTheDocument();
    });
  });
});

describe('Statements Ledger Component', () => {
  it('renders statement records and their statuses', async () => {
    localStorage.setItem('saathi_access_token', 'mock_token');
    localStorage.setItem('saathi_selected_shop_id', 'shop-123');

    vi.mocked(statementsApi.listStatements).mockResolvedValue({
      success: true,
      count: 1,
      data: [
        {
          id: 'stmt-1',
          shop_id: 'shop-123',
          actor_id: 'user-1',
          product_id: 'p-1',
          voice_profile_id: null,
          speaker_status: 'IDENTIFIED',
          speaker_confidence: 0.95,
          transcript: 'Sold 5 bags of rice',
          raw_claim: null,
          quantity: 5.0,
          unit: 'bag',
          direction: 'OUT',
          status: 'CONFIRMED',
          decision: 'AUTO_CONFIRMED',
          source: 'MOBILE_WEB',
          is_overridden: false,
          created_at: '2026-09-19T10:00:00Z',
          updated_at: '2026-09-19T10:00:00Z',
        },
      ],
    });

    vi.mocked(productsApi.listProducts).mockResolvedValue({
      success: true,
      data: [{ id: 'p-1', shop_id: 'shop-123', name: 'Basmati Rice', default_unit: 'bag', is_active: true, created_at: '', updated_at: '' }],
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <Statements />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('"Sold 5 bags of rice"')).toBeInTheDocument();
      expect(screen.getAllByText('CONFIRMED').length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText('IDENTIFIED')).toBeInTheDocument();
    });
  });
});
