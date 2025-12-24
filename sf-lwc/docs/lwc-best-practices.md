# Lightning Web Components Best Practices

## Component Design Principles

### 1. Single Responsibility

Each component should do one thing well.

```
✅ GOOD: accountCard, accountList, accountForm (separate components)
❌ BAD: accountManager (does display, list, and form in one)
```

### 2. Composition Over Inheritance

Build complex UIs by composing simple components.

```html
<!-- Compose components -->
<template>
    <c-page-header title="Accounts"></c-page-header>
    <c-account-filters onfilter={handleFilter}></c-account-filters>
    <c-account-list accounts={filteredAccounts}></c-account-list>
    <c-pagination total={totalCount} onpage={handlePage}></c-pagination>
</template>
```

### 3. Unidirectional Data Flow

Data flows down (props), events bubble up.

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA FLOW PATTERN                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Parent Component                                               │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  state: accounts = [...]                                │   │
│   │                                                          │   │
│   │  ┌──────────┐     ┌──────────┐     ┌──────────┐        │   │
│   │  │ Child A  │ ←── │ Child B  │ ←── │ Child C  │        │   │
│   │  │          │     │          │     │          │        │   │
│   │  │ @api     │     │ @api     │     │ @api     │        │   │
│   │  │ accounts │     │ selected │     │ details  │        │   │
│   │  └────┬─────┘     └────┬─────┘     └────┬─────┘        │   │
│   │       │                │                │               │   │
│   │       │   Events       │   Events       │   Events      │   │
│   │       └────────────────┴────────────────┘               │   │
│   │              ↑ bubbles to parent                        │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Handling

### Wire vs Imperative Apex

| Scenario | Use |
|----------|-----|
| Display data (read-only) | `@wire` with `cacheable=true` |
| Create/Update/Delete | Imperative call |
| Conditional fetching | Imperative call |
| Need to control timing | Imperative call |

### Wire Service Best Practices

```javascript
// Store wire result for refreshApex
wiredAccountsResult;

@wire(getAccounts, { searchTerm: '$searchTerm' })
wiredAccounts(result) {
    this.wiredAccountsResult = result;  // Store for refresh
    const { data, error } = result;
    if (data) {
        this.accounts = data;
        this.error = undefined;
    } else if (error) {
        this.error = error;
        this.accounts = [];
    }
}

// Refresh when needed
async handleRefresh() {
    await refreshApex(this.wiredAccountsResult);
}
```

### Error Handling Pattern

```javascript
// Centralized error reducer
reduceErrors(errors) {
    if (!Array.isArray(errors)) {
        errors = [errors];
    }

    return errors
        .filter(error => !!error)
        .map(error => {
            // UI API errors
            if (error.body && typeof error.body.message === 'string') {
                return error.body.message;
            }
            // JS errors
            if (typeof error.message === 'string') {
                return error.message;
            }
            // Unknown format
            return JSON.stringify(error);
        })
        .join(', ');
}
```

---

## Event Patterns

### Custom Events

```javascript
// Child dispatches event
this.dispatchEvent(new CustomEvent('select', {
    detail: { recordId: this.recordId },
    bubbles: true,    // Bubbles through DOM
    composed: true    // Crosses shadow boundary
}));

// Parent handles event
handleSelect(event) {
    const recordId = event.detail.recordId;
}
```

### Event Naming Conventions

```
✅ GOOD                    ❌ BAD
────────────────────────   ────────────────────────
onselect                   onSelectItem
onrecordchange             on-record-change
onsave                     onSaveClicked
onerror                    onErrorOccurred
```

### When to Use LMS vs Events

| Scenario | Use |
|----------|-----|
| Parent-child communication | Custom events |
| Sibling components (same parent) | Events via parent |
| Components on different parts of page | Lightning Message Service |
| LWC to Aura communication | LMS |
| LWC to Visualforce | LMS |

---

## Performance Optimization

### 1. Lazy Loading

```html
<!-- Only render when needed -->
<template if:true={showDetails}>
    <c-expensive-component record-id={recordId}></c-expensive-component>
</template>
```

### 2. Debouncing

```javascript
delayTimeout;

handleSearch(event) {
    const searchTerm = event.target.value;
    clearTimeout(this.delayTimeout);

    this.delayTimeout = setTimeout(() => {
        this.searchTerm = searchTerm;
    }, 300);  // 300ms debounce
}
```

### 3. Efficient Rendering

```javascript
// Bad: Creates new array every render
get filteredItems() {
    return this.items.filter(item => item.active);
}

// Good: Cache the result
_filteredItems;
_itemsHash;

get filteredItems() {
    const currentHash = JSON.stringify(this.items);
    if (currentHash !== this._itemsHash) {
        this._filteredItems = this.items.filter(item => item.active);
        this._itemsHash = currentHash;
    }
    return this._filteredItems;
}
```

### 4. Virtual Scrolling for Large Lists

Use `lightning-datatable` with `enable-infinite-loading` for large datasets instead of rendering all items.

---

## Security Best Practices

### 1. FLS Enforcement

```apex
// Always use SECURITY_ENFORCED or stripInaccessible
@AuraEnabled(cacheable=true)
public static List<Account> getAccounts() {
    return [SELECT Id, Name FROM Account WITH SECURITY_ENFORCED];
}

// Or use stripInaccessible for DML
SObjectAccessDecision decision = Security.stripInaccessible(
    AccessType.CREATABLE,
    records
);
insert decision.getRecords();
```

### 2. Input Sanitization

```javascript
// Escape user input before using in queries
handleSearch(event) {
    // Don't pass directly to Apex
    const userInput = event.target.value;
    // Apex should escape: String.escapeSingleQuotes(searchTerm)
}
```

### 3. Avoid XSS

```html
<!-- Safe: LWC auto-escapes -->
<p>{userInput}</p>

<!-- Dangerous: Never use innerHTML with user data -->
<!-- LWC doesn't support innerHTML anyway -->
```

---

## Accessibility (a11y)

### Required Practices

| Element | Requirement |
|---------|-------------|
| Buttons | `label` or `aria-label` |
| Icons | `alternative-text` |
| Form inputs | Associated `<label>` |
| Dynamic content | `aria-live` region |
| Loading states | `aria-busy="true"` |

### Keyboard Navigation

```javascript
handleKeyDown(event) {
    switch (event.key) {
        case 'Enter':
        case ' ':  // Space
            this.handleSelect(event);
            break;
        case 'Escape':
            this.handleClose();
            break;
        case 'ArrowDown':
            this.focusNext();
            event.preventDefault();
            break;
        case 'ArrowUp':
            this.focusPrevious();
            event.preventDefault();
            break;
    }
}
```

### Screen Reader Announcements

```html
<!-- Announce changes to screen readers -->
<div aria-live="polite" class="slds-assistive-text">
    {statusMessage}
</div>
```

---

## Testing Checklist

### Unit Test Coverage

- [ ] Component renders without errors
- [ ] Data displays correctly when loaded
- [ ] Error state displays when fetch fails
- [ ] Empty state displays when no data
- [ ] Events dispatch with correct payload
- [ ] User interactions work correctly
- [ ] Loading states are shown/hidden appropriately

### Manual Testing

- [ ] Works in Lightning Experience
- [ ] Works in Salesforce Mobile
- [ ] Works in Experience Cloud (if targeted)
- [ ] Keyboard navigation works
- [ ] Screen reader announces properly
- [ ] No console errors
- [ ] Performance acceptable with real data

---

## Common Mistakes

### 1. Modifying @api Properties

```javascript
// ❌ BAD: Don't modify @api properties directly
@api items;
handleClick() {
    this.items.push(newItem);  // Mutation!
}

// ✅ GOOD: Create new array
handleClick() {
    this.items = [...this.items, newItem];
}
```

### 2. Forgetting to Clean Up

```javascript
// ❌ BAD: Memory leak
connectedCallback() {
    this.subscription = subscribe(...);
}

// ✅ GOOD: Clean up in disconnectedCallback
disconnectedCallback() {
    unsubscribe(this.subscription);
}
```

### 3. Wire with Non-Reactive Parameters

```javascript
// ❌ BAD: Variable not reactive
let recordId = '001xxx';
@wire(getRecord, { recordId: recordId })  // Won't update

// ✅ GOOD: Use class property with $
@api recordId;
@wire(getRecord, { recordId: '$recordId' })  // Reactive
```

### 4. Async in Getters

```javascript
// ❌ BAD: Getters should be synchronous
get data() {
    return await fetchData();  // Error!
}

// ✅ GOOD: Use wire or imperative with state
data;
async connectedCallback() {
    this.data = await fetchData();
}
```

---

## CLI Commands Quick Reference

```bash
# Create new component
sf lightning generate component --name myComponent --type lwc

# Run Jest tests
sf lightning lwc test run

# Run specific test
sf lightning lwc test run --spec path/to/test.js

# Watch mode
sf lightning lwc test run --watch

# Deploy
sf project deploy start --source-dir force-app/main/default/lwc/myComponent
```

---

## Resources

- [LWC Developer Guide](https://developer.salesforce.com/docs/component-library/documentation/en/lwc)
- [Lightning Design System](https://www.lightningdesignsystem.com/)
- [LWC Recipes](https://github.com/trailheadapps/lwc-recipes)
- [LWC Jest Guide](https://developer.salesforce.com/docs/component-library/documentation/en/lwc/lwc.unit_testing_using_jest)
