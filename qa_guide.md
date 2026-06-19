# PhonePe Payment Insights - Q&A Reference Guide

This reference guide contains comprehensive answers and solutions for the SQL, Power BI, and Tableau questions listed in the project outline.

---

## Part 1: SQL Questions & Answers

### Basic

#### 1. What is the difference between WHERE and HAVING?
*   **`WHERE`**: Filters rows *before* any grouping or aggregation takes place. It operates on individual rows. It cannot be used with aggregate functions (like `SUM`, `AVG`, `COUNT`).
*   **`HAVING`**: Filters groups or aggregated results *after* the `GROUP BY` clause has been applied. It operates on summarized rows.
*   *Example:*
    ```sql
    -- WHERE filters raw rows; HAVING filters aggregated groups
    SELECT state, SUM(transaction_amount) 
    FROM agg_trans
    WHERE year = 2023 -- Filters rows first
    GROUP BY state
    HAVING SUM(transaction_amount) > 1000000000; -- Filters groups last
    ```

#### 2. What are PRIMARY KEY and FOREIGN KEY?
*   **PRIMARY KEY (PK)**: A column (or set of columns) that uniquely identifies each row in a table. It must contain unique, non-null values. A table can have only one Primary Key.
*   **FOREIGN KEY (FK)**: A column in one table that links to the Primary Key of another table. It establishes a parent-child relationship between tables and enforces referential integrity.

#### 3. Explain INNER JOIN, LEFT JOIN, RIGHT JOIN, and FULL JOIN.
*   **`INNER JOIN`**: Returns only the rows that have matching values in both tables.
*   **`LEFT JOIN` (or LEFT OUTER JOIN)**: Returns all rows from the left table, and the matched rows from the right table. If no match is found, NULLs are returned for the right table columns.
*   **`RIGHT JOIN` (or RIGHT OUTER JOIN)**: Returns all rows from the right table, and the matched rows from the left table. (Note: SQLite does not support RIGHT JOIN natively; it is accomplished by reversing the table order in a LEFT JOIN).
*   **`FULL JOIN` (or FULL OUTER JOIN)**: Returns all rows when there is a match in either the left or right table. If there is no match, NULLs fill the missing side.

#### 4. What is GROUP BY and when is it used?
*   The `GROUP BY` clause groups rows that have the same values in specified columns into summary rows (e.g., finding the total transactions per state).
*   It is used in conjunction with aggregate functions (`COUNT`, `SUM`, `AVG`, `MAX`, `MIN`) to perform calculations across subsets of data.

#### 5. What is normalization and why is it important?
*   **Normalization** is the process of structuring a relational database in accordance with a series of normal forms (e.g., 1NF, 2NF, 3NF) to reduce data redundancy and improve data integrity.
*   It is important because it prevents data anomalies (Insertion, Update, and Deletion anomalies) and ensures that each data point is stored in exactly one logical place.

---

### Intermediate

#### 1. How do you find the top 5 states by total transaction amount?
*   Aggregate transaction amount using `SUM()`, group by `state`, sort in descending order, and limit the result to 5.
    ```sql
    SELECT state, SUM(transaction_amount) AS total_amount
    FROM agg_trans
    GROUP BY state
    ORDER BY total_amount DESC
    LIMIT 5;
    ```

#### 2. How to calculate month-over-month (or quarter-over-quarter) growth in SQL?
*   Use the `LAG()` window function to retrieve the previous period's transaction amount, then apply the growth formula: `((Current - Previous) / Previous) * 100`.
    ```sql
    WITH quarterly_sales AS (
        SELECT year, quarter, SUM(transaction_amount) AS current_amount
        FROM agg_trans
        GROUP BY year, quarter
    )
    SELECT 
        year, quarter, current_amount,
        LAG(current_amount, 1) OVER (ORDER BY year, quarter) AS prev_amount,
        ROUND(((current_amount - LAG(current_amount, 1) OVER (ORDER BY year, quarter)) / 
               LAG(current_amount, 1) OVER (ORDER BY year, quarter)) * 100, 2) || '%' AS growth
    FROM quarterly_sales;
    ```

#### 3. What is a subquery? Give an example.
*   A **subquery** (or nested query) is a query within another SQL query, typically placed in the `SELECT`, `FROM`, `WHERE`, or `HAVING` clause.
*   *Example (Find transactions that are higher than the average transaction amount):*
    ```sql
    SELECT state, year, quarter, transaction_amount
    FROM agg_trans
    WHERE transaction_amount > (SELECT AVG(transaction_amount) FROM agg_trans);
    ```

#### 4. Difference between COUNT(*) and COUNT(column_name)?
*   **`COUNT(*)`**: Counts every row in the table, including rows with `NULL` values and duplicate records.
*   **`COUNT(column_name)`**: Counts only the rows where the specified column is **not NULL**.

#### 5. How do indexes improve query performance?
*   Indexes act like a book index. They create a sorted data structure (usually a B-Tree) that allows the database engine to find specific rows quickly without scanning the entire table (Full Table Scan).
*   *Trade-off:* While indexes speed up read operations (`SELECT`), they slow down write operations (`INSERT`, `UPDATE`, `DELETE`) because the index must be updated.

---

### Advanced

#### 1. What are window functions? Explain ROW_NUMBER(), RANK(), and DENSE_RANK().
*   **Window functions** perform calculations across a set of table rows that are related to the current row, without collapsing them into a single summary row (retains row identity).
*   **`ROW_NUMBER()`**: Assigns a unique sequential integer starting at 1, regardless of duplicate values. (e.g., 1, 2, 3, 4)
*   **`RANK()`**: Assigns the same rank to duplicate values. However, it leaves gaps in the ranking sequence. (e.g., 1, 2, 2, 4)
*   **`DENSE_RANK()`**: Assigns the same rank to duplicate values without leaving any gaps. (e.g., 1, 2, 2, 3)

#### 2. Write a query to find duplicate transactions.
*   Define what makes a record a duplicate (e.g., same state, date, and amount) and filter groups where `COUNT(*) > 1`.
    ```sql
    SELECT state, year, quarter, transaction_type, transaction_amount, COUNT(*)
    FROM agg_trans
    GROUP BY state, year, quarter, transaction_type, transaction_amount
    HAVING COUNT(*) > 1;
    ```

#### 3. How do you handle NULL values in SQL?
*   **`IS NULL` / `IS NOT NULL`**: Conditional filters.
*   **`COALESCE(val1, val2, ...)`**: Returns the first non-null value in the argument list.
*   **`IFNULL(col, default)`**: (SQLite/MySQL specific) Replaces NULL with a default.
*   **`CASE WHEN col IS NULL THEN default ELSE col END`**: Standard conditional logic.

#### 4. Explain CTEs (WITH clause) and their advantages.
*   A **Common Table Expression (CTE)** is a temporary, named result set that exists solely within the execution scope of a single query.
*   *Advantages:*
    *   Improves readability by breaking complex queries into modular blocks.
    *   Can reference itself (recursive CTEs) for hierarchical data structures.
    *   Serves as an alternative to nested subqueries.

#### 5. How would you optimize a slow-running SQL query?
1.  **Analyze Execution Plan**: Run `EXPLAIN QUERY PLAN` to see if it performs table scans.
2.  **Add Indexes**: Index columns frequently used in `JOIN`, `WHERE`, `ORDER BY`, or `GROUP BY`.
3.  **Avoid `SELECT *`**: Retrieve only the columns needed to minimize I/O load.
4.  **Rewrite Joins**: Ensure joins are on matching data types, and filter data early in CTEs.
5.  **Use Aggregations Wisely**: Avoid complex operations inside calculations (like math on string columns).

---

## Part 2: Power BI Questions & Answers

### Basic

#### 1. What is Power BI and its main components?
Power BI is a business intelligence platform developed by Microsoft that visualizes raw data into interactive insights. Its core components are:
*   **Power BI Desktop**: Development environment.
*   **Power BI Service**: Cloud-based sharing/collaboration portal.
*   **Power BI Mobile**: Viewing app for iOS/Android.
*   **Power Query**: ETL tool.
*   **Power BI Gateway**: Bridges local data with the cloud service for updates.

#### 2. Difference between Power BI Desktop, Service, and Mobile.
*   **Desktop**: Used for data ingestion, cleaning, data modeling, writing DAX, and building reports. (Free, local).
*   **Service**: Used to host reports, pin visuals to dashboards, share with other users, set up row-level security, and schedule refreshes. (Cloud-based, requires Pro/Premium license).
*   **Mobile**: Read-only companion app designed to view dashboard tiles and reports on mobile form factors.

#### 3. What is Power Query?
*   Power Query is the data transformation and preparation engine in Power BI. It uses the **M** formula language to extract, transform, and load (ETL) data, allowing users to pivot, merge, split, and clean datasets before loading them.

#### 4. What are filters and slicers?
*   **Filters**: Applied in the filter pane. They restrict data at the Visual, Page, or Report level, and can be hidden from end-users.
*   **Slicers**: Interactive visual controls placed directly on the canvas. They allow users to slice data dynamically by clicking values (e.g., picking a specific Year).

#### 5. What is a dashboard vs a report?
*   **Report**: A multi-page document built from a single dataset. It contains fully interactive charts that cross-filter each other. Built in Desktop or Service.
*   **Dashboard**: A single-page canvas in the Power BI Service. It consists of "tiles" pinned from *multiple* different reports. It provides a high-level KPI overview and is not highly interactive (clicking a tile redirects you to the source report).

---

### Intermediate

#### 1. Explain data modeling in Power BI.
*   Data modeling involves connecting multiple tables using relationships, configuring their properties (cardinality and cross-filter direction), and organizing data structures (like schemas) so DAX expressions evaluate efficiently.

#### 2. What are relationships and their types?
Relationships define how tables connect based on common keys:
*   **One-to-Many (1:*)**: The most common. One row in the dimension table relates to many rows in the fact table.
*   **One-to-One (1:1)**: Link between two unique records.
*   **Many-to-Many (*:*)**: Links multiple matching rows. Should be avoided if possible as it degrades performance and can introduce ambiguity.
*   **Cross-Filter Direction**:
    *   *Single*: Filter flows in one direction (usually from Dimension to Fact table).
    *   *Bi-directional*: Filter flows in both directions. Use sparingly as it can lead to performance issues and circular dependencies.

#### 3. Difference between calculated column and measure.
*   **Calculated Column**: Computes values row-by-row during data load. It is stored in the database memory, consuming RAM and file size.
*   **Measure**: Computes values on-the-fly dynamically based on user interaction (visual filter context). It does not consume storage space.

#### 4. What is DAX?
*   **DAX (Data Analysis Expressions)** is the formula language used in Power BI, Analysis Services, and Excel Power Pivot to build custom calculations, aggregates, and key performance metrics.

#### 5. How do you calculate YTD, MTD, QTD in Power BI?
*   Use Time Intelligence DAX functions along with a standard Date table:
    ```dax
    -- Year-to-Date (YTD) Measure
    Total_YTD_Amount = TOTALYTD(SUM(agg_trans[transaction_amount]), 'Calendar'[Date])
    ```
    Similarly, use `TOTALMTD()` and `TOTALQTD()` for Month-to-Date and Quarter-to-Date.

---

### Advanced

#### 1. What is Row-Level Security (RLS)?
*   RLS filters data at the database level so specific users can only see rows they have permission to access. In Power BI Desktop, you define roles using DAX rules (e.g., `[state] = "Maharashtra"`). In Power BI Service, you assign users or Azure AD groups to those roles.

#### 2. Explain STAR schema and why it is used.
*   A **STAR Schema** consists of a central **Fact table** containing measurable quantities (amounts, counts) surrounded by **Dimension tables** containing descriptive attributes (dates, locations, categories).
*   *Why it is used:* It is the gold standard for Power BI because the VertiPaq engine is optimized for it. It minimizes joins, simplifies DAX writing, and delivers the fastest query rendering times.

#### 3. Difference between Import mode and DirectQuery.
*   **Import Mode**: Ingests and compresses all data into the Power BI memory. It is extremely fast, supports all DAX features, but requires periodic data refreshes and has file size limits.
*   **DirectQuery**: Does not load data. It queries the database in real-time. It supports live data updates and very large datasets, but report interactivity depends on database speed and DAX options are limited.

#### 4. How do you optimize Power BI report performance?
1.  Use Star Schema rather than flat tables.
2.  Reduce column counts—remove unused columns in Power Query.
3.  Use Measures instead of Calculated Columns where possible.
4.  Limit the number of visuals per page to prevent rendering queues.
5.  Use **Performance Analyzer** to find slow DAX queries or slow rendering visuals.

#### 5. Explain context (row context vs filter context) in DAX.
*   **Row Context**: Occurs when a formula iterates row-by-row (e.g., inside a calculated column or an iterator function like `SUMX`). It only knows the values of the current row.
*   **Filter Context**: The set of filters active in the report visual. It is established by slicers, table headers, visual selections, and modified via the `CALCULATE()` function.

---

## Part 3: Tableau Questions & Answers

### Basic

#### 1. What is Tableau and how does it work?
*   Tableau is a data visualization software. It connects to various databases, pulls data, translates drag-and-drop actions into SQL queries (using VizQL), and renders interactive charts, dashboards, and stories.

#### 2. Difference between discrete and continuous data.
*   **Discrete (Blue pills)**: Represents individually separate and distinct values (e.g., categories, states). Creates headers in the view.
*   **Continuous (Green pills)**: Represents an infinite range of values (e.g., sales, profit, temperature). Creates axes in the view.

#### 3. What are dimensions and measures?
*   **Dimensions**: Categorical or qualitative data fields (e.g., Category, Region, Date). They slice, group, or detail the visualization.
*   **Measures**: Numerical or quantitative data fields (e.g., Sales, Quantity). They are aggregated when placed in the view.

#### 4. What are shelves in Tableau?
*   Shelves are designated areas where fields (pills) are dropped to build a chart. Key shelves include: **Rows**, **Columns**, **Pages**, **Filters**, and the **Marks Card** (which controls Color, Size, Text, Detail, and Tooltip).

#### 5. What is a worksheet, dashboard, and story?
*   **Worksheet**: A single sheet where you build a single visualization.
*   **Dashboard**: A collection of worksheets arranged on a single screen to show multiple related views.
*   **Story**: A sequence of dashboards or sheets arranged in a timeline format to guide the user through a narrative.

---

### Intermediate

#### 1. What are joins vs blends in Tableau?
*   **Join**: Combines tables at the row level. It works within a *single* data source.
*   **Blend**: Combines data from *different* data sources (e.g., Excel and SQL Server) at the sheet level. It aggregates the secondary data source to match the level of detail of the primary data source, behaving like a `LEFT JOIN`.

#### 2. What is a calculated field?
*   A calculated field is a new column created in Tableau using formulas based on existing fields (e.g., `[Sales] - [Cost]`).

#### 3. What are parameters and why are they used?
*   Parameters are dynamic values that a user can interactively select (like a dropdown list or textbox) to replace constant values in calculations, filters, or reference lines.

#### 4. Explain filters order of operations.
Tableau executes filters in this exact order:
1.  **Extract Filters**
2.  **Data Source Filters**
3.  **Context Filters**
4.  **Dimension Filters**
5.  **Measure Filters**
6.  **Table Calculation Filters**

#### 5. What is a dual-axis chart?
*   A dual-axis chart plots two measures in a single visualization using two independent Y-axes (one on the left, one on the right) sharing a single X-axis. Used to compare metrics with different scales (e.g., Sales vs. Profit Margin).

---

### Advanced

#### 1. What are LOD expressions (FIXED, INCLUDE, EXCLUDE)?
LOD (Level of Detail) expressions allow you to run aggregate queries at specific dimensions without relying on the worksheet structure:
*   **`FIXED`**: Computes values using specified dimensions, completely ignoring whatever dimensions are in the worksheet view.
*   **`INCLUDE`**: Computes values using specified dimensions in addition to whatever dimensions are in the view.
*   **`EXCLUDE`**: Computes values omitting the specified dimensions, even if they are in the view.

#### 2. How do you handle large datasets in Tableau?
1.  Create a **Tableau Extract** (.hyper) instead of a live connection.
2.  Use extract filters to limit rows.
3.  Hide all unused fields to shrink extract size.
4.  Avoid complex string comparisons; convert categories to integers if possible.
5.  Use context filters to reduce the dataset size before other filters execute.

#### 3. Difference between extracts and live connections.
*   **Extract**: A compressed snapshot of data saved locally or in the Tableau server. Faster, allows offline analysis, but must be refreshed.
*   **Live**: Queries the source database directly in real-time. Reflects changes immediately, but performance is limited by the source database's speed.

#### 4. How do you implement row-level security in Tableau?
*   Create a calculated field using user functions like `USERNAME()` or `USERMEMBERGROUP()`.
*   *Example:* `[Sales Region] = USERNAME()`
*   Place this calculated field on the Data Source Filters shelf, setting it to `TRUE`.

#### 5. How do you optimize dashboard performance?
1.  Keep the number of sheets in a dashboard under 6.
2.  Use fixed-size dashboards rather than automatic sizing to prevent re-rendering.
3.  Minimize nested table calculations and LODs.
4.  Avoid placing too many marks on a map or scatterplot.
5.  Remove unused sheets and dashboards from the workbook.
