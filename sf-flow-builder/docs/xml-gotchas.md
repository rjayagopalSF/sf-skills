# Salesforce Flow XML Metadata Gotchas

Critical XML metadata constraints and known issues when deploying flows via Metadata API.

## storeOutputAutomatically Data Leak Risk (v2.0.0)

**⚠️ SECURITY WARNING**: When `storeOutputAutomatically="true"` in recordLookups, **ALL fields** are retrieved and stored.

### Risks

1. **Data Leak**: Sensitive fields (SSN, salary, etc.) may be exposed unintentionally
2. **Performance**: Large objects with many fields impact query performance
3. **Screen Flow Exposure**: In screen flows, external users could access all data

### Recommended Pattern

**Always specify only the fields you need:**

```xml
<recordLookups>
    <name>Get_Account</name>
    <!-- Specify exact fields needed -->
    <queriedFields>Id</queriedFields>
    <queriedFields>Name</queriedFields>
    <queriedFields>Industry</queriedFields>
    <!-- Store in explicit variable -->
    <outputReference>rec_Account</outputReference>
</recordLookups>
```

**Avoid:**
```xml
<recordLookups>
    <name>Get_Account</name>
    <!-- Retrieves ALL fields - security risk! -->
    <storeOutputAutomatically>true</storeOutputAutomatically>
</recordLookups>
```

---

## Relationship Fields Not Supported in recordLookups (CRITICAL)

**⚠️ DEPLOYMENT BLOCKER**: Flow's Get Records (recordLookups) CANNOT query parent relationship fields.

### What Doesn't Work

```xml
<!-- ❌ THIS WILL FAIL DEPLOYMENT -->
<recordLookups>
    <name>Get_User</name>
    <object>User</object>
    <queriedFields>Id</queriedFields>
    <queriedFields>Name</queriedFields>
    <queriedFields>Manager.Name</queriedFields>  <!-- FAILS! -->
</recordLookups>
```

**Error**: `field integrity exception: unknown (The field "Manager.Name" for the object "User" doesn't exist.)`

### Why It Fails

- Flow's recordLookups only supports direct fields on the queried object
- Parent relationship traversal (dot notation like `Parent.Field`) is NOT supported
- This is different from SOQL in Apex which supports relationship queries

### Fields That WON'T Work

| Object | Invalid Field | Error |
|--------|---------------|-------|
| User | `Manager.Name` | Manager.Name doesn't exist |
| Contact | `Account.Name` | Account.Name doesn't exist |
| Case | `Account.Owner.Email` | Account.Owner.Email doesn't exist |
| Opportunity | `Account.Industry` | Account.Industry doesn't exist |

### Correct Solution: Two-Step Query

```xml
<!-- Step 1: Get the child record with lookup ID -->
<recordLookups>
    <name>Get_User</name>
    <object>User</object>
    <queriedFields>Id</queriedFields>
    <queriedFields>Name</queriedFields>
    <queriedFields>ManagerId</queriedFields>  <!-- ✅ Get the ID only -->
    <outputReference>rec_User</outputReference>
</recordLookups>

<!-- Step 2: Query parent record using the lookup ID -->
<recordLookups>
    <name>Get_Manager</name>
    <object>User</object>
    <filters>
        <field>Id</field>
        <operator>EqualTo</operator>
        <value>
            <elementReference>rec_User.ManagerId</elementReference>
        </value>
    </filters>
    <queriedFields>Id</queriedFields>
    <queriedFields>Name</queriedFields>
    <outputReference>rec_Manager</outputReference>
</recordLookups>
```

### Flow Routing

Ensure your flow checks for null before using the parent record:
```xml
<decisions>
    <name>Check_Manager_Exists</name>
    <rules>
        <conditions>
            <leftValueReference>rec_Manager</leftValueReference>
            <operator>IsNull</operator>
            <rightValue><booleanValue>false</booleanValue></rightValue>
        </conditions>
    </rules>
</decisions>
```

---

## $Record vs $Record__c Confusion (Record-Triggered Flows)

**⚠️ COMMON MISTAKE**: Confusing Flow's `$Record` with Process Builder's `$Record__c`.

### What's the Difference?

| Variable | Context | Usage |
|----------|---------|-------|
| `$Record` | Flow (Record-Triggered) | Single record that triggered the flow |
| `$Record__c` | Process Builder | Collection of records in trigger batch |

### The Mistake

Trying to create a loop over `$Record__c` in a Flow:

```xml
<!-- ❌ THIS DOES NOT EXIST IN FLOWS -->
<loops>
    <collectionReference>$Record__c</collectionReference>  <!-- INVALID! -->
</loops>
```

### Why This Happens

- Process Builder used `$Record__c` to represent the batch of triggering records
- Developers migrating from Process Builder assume Flows work the same way
- In Flows, `$Record` is always a **single record**, not a collection
- The platform handles bulk batching automatically

### Correct Approach in Record-Triggered Flows

**Use `$Record` directly without loops:**

```xml
<!-- ✅ CORRECT: Direct access to triggered record -->
<decisions>
    <conditions>
        <leftValueReference>$Record.StageName</leftValueReference>
        <operator>EqualTo</operator>
        <rightValue><stringValue>Closed Won</stringValue></rightValue>
    </conditions>
</decisions>

<!-- ✅ Build task using $Record fields -->
<assignments>
    <assignmentItems>
        <assignToReference>rec_Task.WhatId</assignToReference>
        <value><elementReference>$Record.Id</elementReference></value>
    </assignmentItems>
</assignments>
```

### When You DO Need Loops

Only when processing **related records**, not the triggered record:

```xml
<!-- ✅ CORRECT: Loop over RELATED records -->
<recordLookups>
    <filters>
        <field>AccountId</field>
        <value><elementReference>$Record.AccountId</elementReference></value>
    </filters>
    <outputReference>col_RelatedContacts</outputReference>
</recordLookups>

<loops>
    <collectionReference>col_RelatedContacts</collectionReference>  <!-- ✅ Valid -->
</loops>
```

---

## recordLookups Conflicts

**NEVER use both** `<storeOutputAutomatically>` AND `<outputReference>` together.

**Choose ONE approach:**
```xml
<!-- Option 1: Auto-store (creates variable automatically) - NOT RECOMMENDED -->
<storeOutputAutomatically>true</storeOutputAutomatically>

<!-- Option 2: Explicit variable - RECOMMENDED -->
<outputReference>rec_AccountRecord</outputReference>
```

## Element Ordering in recordLookups

Elements must follow this order:
1. `<name>` 2. `<label>` 3. `<locationX>` 4. `<locationY>` 5. `<assignNullValuesIfNoRecordsFound>` 6. `<connector>` 7. `<filterLogic>` 8. `<filters>` 9. `<getFirstRecordOnly>` 10. `<object>` 11. `<outputReference>` OR `<storeOutputAutomatically>` 12. `<queriedFields>`

## Transform Element

**Recommendation**: Create Transform elements in Flow Builder UI, then deploy - do NOT hand-write.

Issues with hand-written Transform:
- Complex nested XML structure with strict ordering
- `inputReference` placement varies by context
- Multiple conflicting rules in Metadata API

## Subflow Calling Limitation (Metadata API Constraint)

**Record-triggered flows (`processType="AutoLaunchedFlow"`) CANNOT call subflows via XML deployment.**

**Root Cause**: Salesforce Metadata API does not support the "flow" action type for AutoLaunchedFlow process types.

**Valid action types for AutoLaunchedFlow**: apex, chatterPost, emailAlert, emailSimple, and platform-specific actions - but NOT "flow".

**Error message**: "You can't use the Flows action type in flows with the Autolaunched Flow process type"

**Screen Flows (`processType="Flow"`) CAN call subflows** successfully via XML deployment.

**UI vs XML**: Flow Builder UI may use different internal mechanisms - UI capabilities may differ from direct XML deployment.

### Recommended Solution for Record-Triggered Flows

Use **inline orchestration** instead of subflows:

1. Organize logic into clear sections with descriptive element naming
2. Pattern: `Decision_CheckCriteria` → `Assignment_SetFields` → `Create_Record`
3. Add XML comments to delineate sections: `<!-- Section 1: Contact Creation -->`

**Benefits**: Single atomic flow, no deployment dependencies, full execution control.

**Reference**: [Salesforce Help Article 000396957](https://help.salesforce.com/s/articleView?id=000396957&type=1)

## Root-Level Element Ordering

Salesforce Metadata API requires **strict alphabetical ordering** at root level:

1. `<apiVersion>`
2. `<assignments>`
3. `<decisions>`
4. `<description>`
5. `<label>`
6. `<loops>`
7. `<processType>`
8. `<recordCreates>`
9. `<recordUpdates>`
10. `<start>`
11. `<status>`
12. `<variables>`

**Note**: API 60.0+ does NOT use `<bulkSupport>` - bulk processing is automatic.

## Common Deployment Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "Element X is duplicated" | Elements not alphabetically ordered | Reorder elements |
| "Element bulkSupport invalid" | Using deprecated element (API 60.0+) | Remove `<bulkSupport>` |
| "Error parsing file" | Malformed XML | Validate XML syntax |
| "field 'X.Y' doesn't exist" | Relationship field in queriedFields | Use two-step query pattern |
| "$Record__Prior can only be used..." | Using $Record__Prior with Create trigger | Change to Update or CreateAndUpdate |
| "You can't use the Flows action type..." | Subflow in AutoLaunchedFlow | Use inline logic instead |

---

## Summary: Lessons Learned

### Relationship Fields
- **Problem**: Querying `Parent.Field` in Get Records
- **Solution**: Two separate queries - child first, then parent by ID

### Record-Triggered Flow Architecture
- **Problem**: Creating loops over triggered records
- **Solution**: Use `$Record` directly - platform handles batching

### Deployment
- **Problem**: Using direct CLI commands
- **Solution**: Always use sf-deployment skill

### $Record Context
- **Problem**: Confusing Flow's `$Record` with Process Builder's `$Record__c`
- **Solution**: `$Record` is single record, use without loops
