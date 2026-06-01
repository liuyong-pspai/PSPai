# L6↔L7 功能调换设计文档

> 2026-05-30 与用户全天头脑风暴产物
> 实施人：Agent

## 调换

| 层级 | 原功能 | 新功能 | 原类名 | 新类名 |
|:---|:---|:---|:---|:---|
| L6 | 推陈出新（去冗） | 悟道觉醒 | L6Renewal | L6Enlightenment |
| L7 | 灵魂升华（觉醒） | 推陈出新（去冗） | L7Sublimation | L7Renewal |

## 逻辑

悟道→去冗，顺序不可逆：
- 悟道需要完整材料（包括看似冗余的）来发现模式
- 去冗需要悟道校准后的判断标准
- 先去冗再悟道 = 用旧标准筛材料 → 悟道只能用二手数据

## 代码证据

旧代码中L6的`dispose_retired`方法删完条目后调用`self._soul_trigger("L6", ...)`通知L7——方向反了。应该是L6悟道产出新标准 → 通知L7执行清理。

## 管线变化

```
旧: L4/L5/L6 → trigger → L7（觉醒能量累加）
新: L6先初始化 → L4/L5/L7注入self.l6.trigger → L6累积觉醒能量
```

## 向后兼容

`from cognition.memory_new import L6Renewal` 和 `L7Sublimation` 仍可用，通过别名指向新类。
