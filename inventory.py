#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一勺食话 | 库存管理系统
核心功能：商品增删改查 + 保质期临期预警
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# 数据文件路径
DATA_FILE = "inventory.json"


class InventoryManager:
    """库存管理器"""

    def __init__(self):
        self.inventory = self._load_data()

    def _load_data(self) -> Dict:
        """从JSON文件加载数据"""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                print(f"⚠️  数据文件损坏，将创建新文件")
        return {}

    def _save_data(self) -> None:
        """保存数据到JSON文件"""
        try:
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.inventory, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"❌ 保存失败：{e}")

    def _get_expiry_date(self, production_date: str, shelf_life_months: int) -> datetime:
        """计算过期日期"""
        prod_date = datetime.strptime(production_date, "%Y-%m-%d")
        # 计算过期日期（生产日期 + 保质期月数）
        expiry_date = prod_date.replace(
            year=prod_date.year + (prod_date.month + shelf_life_months - 1) // 12,
            month=(prod_date.month + shelf_life_months - 1) % 12 + 1
        )
        return expiry_date

    def _check_expiry_status(self, production_date: str, shelf_life_months: int) -> Dict:
        """检查商品保质期状态"""
        today = datetime.now()
        expiry_date = self._get_expiry_date(production_date, shelf_life_months)
        days_remaining = (expiry_date - today).days

        if days_remaining < 0:
            return {"status": "expired", "days": abs(days_remaining), "message": f"⛔ 已过期 {abs(days_remaining)} 天"}
        elif days_remaining <= 30:
            return {"status": "expiring", "days": days_remaining, "message": f"⚠️ 临期，剩余 {days_remaining} 天"}
        else:
            return {"status": "safe", "days": days_remaining, "message": f"✅ 安全，剩余 {days_remaining} 天"}

    def add_product(self, name: str, category: str, stock: int, cost_price: float,
                   sell_price: float, production_date: str, shelf_life_months: int) -> bool:
        """添加商品"""
        if name in self.inventory:
            print(f"❌ 商品 '{name}' 已存在")
            return False

        expiry_status = self._check_expiry_status(production_date, shelf_life_months)

        self.inventory[name] = {
            "category": category,
            "stock": stock,
            "cost_price": cost_price,
            "sell_price": sell_price,
            "production_date": production_date,
            "shelf_life_months": shelf_life_months,
            "expiry_status": expiry_status,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self._save_data()
        print(f"✅ 商品 '{name}' 添加成功！{expiry_status['message']}")
        return True

    def list_products(self) -> None:
        """列出所有商品"""
        if not self.inventory:
            print("📦 库存为空")
            return

        print("\n" + "=" * 90)
        print(f"{'商品名':<15} {'类目':<12} {'库存':<8} {'进价':<8} {'售价':<8} {'保质期':<15}")
        print("=" * 90)

        for name, info in self.inventory.items():
            expiry_msg = info['expiry_status']['message']
            print(f"{name:<15} {info['category']:<12} {info['stock']:<8} "
                  f"¥{info['cost_price']:<7.2f} ¥{info['sell_price']:<7.2f} {expiry_msg:<15}")
        print("=" * 90)
        print(f"共 {len(self.inventory)} 件商品\n")

    def search_product(self, name: str) -> Optional[Dict]:
        """查找单个商品详情"""
        if name not in self.inventory:
            print(f"❌ 未找到商品 '{name}'")
            return None

        info = self.inventory[name]
        expiry_date = self._get_expiry_date(info['production_date'], info['shelf_life_months'])

        print(f"\n{'='*60}")
        print(f"📦 商品详情：{name}")
        print(f"{'='*60}")
        print(f"类目：         {info['category']}")
        print(f"库存：         {info['stock']} 件")
        print(f"进价：         ¥{info['cost_price']:.2f}")
        print(f"售价：         ¥{info['sell_price']:.2f}")
        print(f"生产日期：     {info['production_date']}")
        print(f"保质期：       {info['shelf_life_months']} 个月")
        print(f"过期日期：     {expiry_date.strftime('%Y-%m-%d')}")
        print(f"保质期状态：   {info['expiry_status']['message']}")
        print(f"创建时间：     {info['created_at']}")
        print(f"{'='*60}\n")

        return info

    def update_product(self, name: str, **kwargs) -> bool:
        """更新商品信息"""
        if name not in self.inventory:
            print(f"❌ 未找到商品 '{name}'")
            return False

        # 允许更新的字段
        updatable_fields = {
            'category': '类目',
            'stock': '库存',
            'cost_price': '进价',
            'sell_price': '售价',
            'production_date': '生产日期',
            'shelf_life_months': '保质期（月）'
        }

        updated_fields = []
        for field, value in kwargs.items():
            if field in updatable_fields:
                self.inventory[name][field] = value
                updated_fields.append(updatable_fields[field])

        # 如果更新了生产日期或保质期，重新计算保质期状态
        if 'production_date' in kwargs or 'shelf_life_months' in kwargs:
            expiry_status = self._check_expiry_status(
                self.inventory[name]['production_date'],
                self.inventory[name]['shelf_life_months']
            )
            self.inventory[name]['expiry_status'] = expiry_status
            updated_fields.append('保质期状态')

        if updated_fields:
            self._save_data()
            print(f"✅ 商品 '{name}' 更新成功，已更新：{', '.join(updated_fields)}")
            return True
        else:
            print(f"❌ 未提供有效的更新字段")
            return False

    def delete_product(self, name: str) -> bool:
        """删除商品"""
        if name not in self.inventory:
            print(f"❌ 未找到商品 '{name}'")
            return False

        del self.inventory[name]
        self._save_data()
        print(f"✅ 商品 '{name}' 已删除")
        return True

    def check_expiring_products(self, days_threshold: int = 30) -> None:
        """临期商品预警"""
        today = datetime.now()
        expiring_products = []

        for name, info in self.inventory.items():
            expiry_date = self._get_expiry_date(info['production_date'], info['shelf_life_months'])
            days_remaining = (expiry_date - today).days

            if days_remaining <= days_threshold:
                expiring_products.append({
                    'name': name,
                    'days_remaining': days_remaining,
                    'stock': info['stock'],
                    'expiry_date': expiry_date.strftime('%Y-%m-%d')
                })

        if not expiring_products:
            print(f"✅ 没有临期商品（{days_threshold}天内）\n")
            return

        # 按剩余天数排序
        expiring_products.sort(key=lambda x: x['days_remaining'])

        print(f"\n{'⚠️ 临期商品预警（30天内）':^90}")
        print("=" * 90)

        for product in expiring_products:
            if product['days_remaining'] < 0:
                status = f"🔴 已过期 {abs(product['days_remaining'])} 天"
            else:
                status = f"🟡 剩余 {product['days_remaining']} 天"

            print(f"{product['name']:<20} | 库存: {product['stock']:<6} | "
                  f"过期: {product['expiry_date']:<12} | {status}")

        print("=" * 90)
        print(f"共 {len(expiring_products)} 件临期商品，请及时处理！\n")

    def show_statistics(self) -> None:
        """显示统计信息"""
        if not self.inventory:
            print("📊 暂无数据")
            return

        total_stock = sum(info['stock'] for info in self.inventory.values())
        total_cost = sum(info['cost_price'] * info['stock'] for info in self.inventory.values())
        total_value = sum(info['sell_price'] * info['stock'] for info in self.inventory.values())
        total_profit = total_value - total_cost

        # 统计类目
        categories = {}
        for info in self.inventory.values():
            cat = info['category']
            categories[cat] = categories.get(cat, 0) + info['stock']

        print(f"\n{'📊 库存统计':^60}")
        print("=" * 60)
        print(f"商品总数：     {len(self.inventory)} 种")
        print(f"库存总量：     {total_stock} 件")
        print(f"库存总成本：   ¥{total_cost:.2f}")
        print(f"库存总价值：   ¥{total_value:.2f}")
        print(f"预期总利润：   ¥{total_profit:.2f}")
        print(f"\n{'类目分布':^60}")
        print("-" * 60)
        for cat, count in sorted(categories.items()):
            print(f"  {cat}: {count} 件")
        print("=" * 60 + "\n")


def print_menu():
    """打印主菜单"""
    print("\n" + "=" * 60)
    print(f"{'🥄 一勺食话 | 库存管理系统':^60}")
    print("=" * 60)
    print("1. ➕ 添加商品")
    print("2. 📋 查看所有商品")
    print("3. 🔍 查找商品")
    print("4. ✏️  更新商品")
    print("5. 🗑️  删除商品")
    print("6. ⚠️  临期商品预警")
    print("7. 📊 统计信息")
    print("0. 👋 退出")
    print("=" * 60)


def get_input(prompt: str, input_type=str, default=None):
    """获取用户输入"""
    while True:
        try:
            value = input(prompt).strip()
            if not value and default is not None:
                return default
            if input_type == int:
                return int(value)
            elif input_type == float:
                return float(value)
            return value
        except ValueError:
            print(f"❌ 请输入有效的{input_type.__name__}值")


def main():
    """主程序"""
    manager = InventoryManager()

    print("\n🎉 欢迎使用一勺食话库存管理系统！")

    while True:
        print_menu()
        choice = get_input("请选择操作 (0-7): ", int)

        if choice == 0:
            print("\n👋 再见，祝您生意兴隆！\n")
            break

        elif choice == 1:
            print("\n➕ 添加新商品")
            name = get_input("商品名: ")
            category = get_input("类目: ")
            stock = get_input("库存数量: ", int, 0)
            cost_price = get_input("进价: ", float, 0.0)
            sell_price = get_input("售价: ", float, 0.0)
            production_date = get_input("生产日期 (YYYY-MM-DD): ")
            shelf_life = get_input("保质期（月）: ", int, 12)

            try:
                datetime.strptime(production_date, "%Y-%m-%d")
            except ValueError:
                print("❌ 日期格式错误，请使用 YYYY-MM-DD 格式")
                continue

            manager.add_product(name, category, stock, cost_price, sell_price,
                              production_date, shelf_life)

        elif choice == 2:
            manager.list_products()

        elif choice == 3:
            name = get_input("请输入商品名: ")
            manager.search_product(name)

        elif choice == 4:
            name = get_input("请输入要更新的商品名: ")
            if name not in manager.inventory:
                print(f"❌ 未找到商品 '{name}'")
                continue

            print(f"\n当前商品信息：")
            manager.search_product(name)

            print("\n请输入新值（直接回车保持原值）：")
            updates = {}

            new_category = get_input(f"类目 [{manager.inventory[name]['category']}]: ")
            if new_category:
                updates['category'] = new_category

            new_stock = get_input(f"库存 [{manager.inventory[name]['stock']}]: ", int)
            if new_stock is not None:
                updates['stock'] = new_stock

            new_cost = get_input(f"进价 [{manager.inventory[name]['cost_price']}]: ", float)
            if new_cost is not None:
                updates['cost_price'] = new_cost

            new_sell = get_input(f"售价 [{manager.inventory[name]['sell_price']}]: ", float)
            if new_sell is not None:
                updates['sell_price'] = new_sell

            new_prod_date = get_input(f"生产日期 [{manager.inventory[name]['production_date']}]: ")
            if new_prod_date:
                try:
                    datetime.strptime(new_prod_date, "%Y-%m-%d")
                    updates['production_date'] = new_prod_date
                except ValueError:
                    print("❌ 日期格式错误")

            new_shelf_life = get_input(f"保质期(月) [{manager.inventory[name]['shelf_life_months']}]: ", int)
            if new_shelf_life is not None:
                updates['shelf_life_months'] = new_shelf_life

            if updates:
                manager.update_product(name, **updates)

        elif choice == 5:
            name = get_input("请输入要删除的商品名: ")
            manager.delete_product(name)

        elif choice == 6:
            days = get_input("预警天数 (默认30): ", int, 30)
            manager.check_expiring_products(days)

        elif choice == 7:
            manager.show_statistics()

        else:
            print("❌ 无效选择，请重新输入")


if __name__ == "__main__":
    main()