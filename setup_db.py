import sqlite3

def create_database():
    conn = sqlite3.connect('bakeshop.db')
    cursor = conn.cursor()
    
    # Enable foreign key support in SQLite
    cursor.execute('PRAGMA foreign_keys = ON;')

    sql_script = """
    -- =========================================
    -- TABLES CREATION
    -- =========================================
    
    -- MODULE 1: Supply Chain & Inventory
    CREATE TABLE Suppliers(
        SupplierID INT PRIMARY KEY,
        Name VARCHAR(30),
        Contact_person VARCHAR(30),
        Phone VARCHAR(30),
        Email_address VARCHAR(30)
    );

    CREATE TABLE Ingredient_Categories(
        CategoryID INT PRIMARY KEY,
        CategoryName VARCHAR(50),
        Description VARCHAR(50)
    );

    CREATE TABLE Ingredients(
        IngredientID INT PRIMARY KEY,
        Name VARCHAR(30),
        CategoryID INT,
        unit_of_measure VARCHAR(30),
        Reorder_level VARCHAR(30),
        Current_stock INT,
        FOREIGN KEY (CategoryID) REFERENCES Ingredient_Categories(CategoryID)
    );
     
    CREATE TABLE Purchase_Order(
        PO_ID INT PRIMARY KEY,
        SupplierID INT,
        Order_date DATE,
        Exp_deleivey_date DATE,
        Total_Amount INT,
        Status VARCHAR(20),
        FOREIGN KEY (SupplierID) REFERENCES Suppliers(SupplierID)
    );

    CREATE TABLE Batches (
        BatchID INT PRIMARY KEY,
        IngredientID INT,
        PO_ID INT,
        Receive_date DATE,
        Expiry_date DATE,
        Quantity_Received INT,
        Remaining_Quantity INT,
        FOREIGN KEY (IngredientID) REFERENCES Ingredients(IngredientID),
        FOREIGN KEY (PO_ID) REFERENCES Purchase_Order(PO_ID)
    );

    -- MODULE 2: Product & Recipe (Core)
    CREATE TABLE Product_categories( 
        CategoryID INT PRIMARY KEY,
        Category_Name VARCHAR(50),
        Description VARCHAR(50)
    );

    CREATE TABLE Products (
        ProductID INT PRIMARY KEY,
        Name VARCHAR(30),
        CategoryID INT,
        Description VARCHAR(30),
        Base_Price DECIMAL(8,2),
        is_active INT,
        FOREIGN KEY (CategoryID) REFERENCES Product_categories(CategoryID)
    );

    CREATE TABLE Recipes (
        RecipeID INT PRIMARY KEY,
        ProductID INT,
        IngredientID INT,
        quantity_required DECIMAL(8,2),
        FOREIGN KEY (ProductID) REFERENCES Products(ProductID),
        FOREIGN KEY (IngredientID) REFERENCES Ingredients(IngredientID)
    );

    -- MODULE 3: Sales & Orders
    CREATE TABLE customers (
        CustomerID INT PRIMARY KEY,
        First_Name VARCHAR(30),
        Last_Name VARCHAR(30),
        Phone VARCHAR(30),
        Email VARCHAR(30),
        Registration_Date DATE 
    );

    CREATE TABLE Customer_Addresses(
        AddressID INT PRIMARY KEY,
        CustomerID INT ,
        Address_Line VARCHAR(30),
        City VARCHAR(30),
        Address_Type VARCHAR (30),
        Is_Default INT,
        FOREIGN KEY (CustomerID) REFERENCES customers(CustomerID)
    );

    CREATE TABLE Orders (
        Order_ID INT PRIMARY KEY,
        CustomerID INT,
        Order_Date DATE,
        Total_Amount DECIMAL(8,2),
        Tax_Amount DECIMAL(8,2),
        Discount_Amount DECIMAL(8,2),
        Final_Total DECIMAL(8,2),
        FOREIGN KEY (CustomerID) REFERENCES customers(CustomerID)
    );

    CREATE TABLE Order_Details(
        Order_Detail_ID INT PRIMARY KEY,
        Order_ID INT,
        ProductID INT ,
        Quantity INT,
        Unit_Price DECIMAL(8,3),
        Line_Total DECIMAL(8,3),
        FOREIGN KEY (Order_ID) REFERENCES Orders(Order_ID),
        FOREIGN KEY (ProductID) REFERENCES Products(ProductID)
    );

    CREATE TABLE payments (
        Payment_ID INT PRIMARY KEY,
        Order_ID INT ,
        Payment_Date DATE,
        Amount_Paid INT,
        Payment_Status INT,
        FOREIGN KEY (Order_ID) REFERENCES Orders(Order_ID)
    );

    -- MODULE 4: Delivery & Tracking
    CREATE TABLE Delivery_Riders(
        Rider_ID INT PRIMARY KEY,
        First_Name VARCHAR(30),
        Last_Name VARCHAR(30),
        Phone VARCHAR(30),
        Vehicle_Type VARCHAR(30)
    );

    CREATE TABLE Deliveries(
        Delivery_ID INT PRIMARY KEY,
        Order_ID INT,
        Rider_ID INT,
        AddressID INT,
        Dispatch_Time VARCHAR(60),
        Delivery_Time VARCHAR(60),
        Delivery_Status INT,
        FOREIGN KEY (Order_ID) REFERENCES Orders(Order_ID),
        FOREIGN KEY (Rider_ID) REFERENCES Delivery_Riders(Rider_ID),
        FOREIGN KEY (AddressID) REFERENCES Customer_Addresses(AddressID)
    );

    -- MODULE 5: HR & Kitchen Operations
    CREATE TABLE Employees(
        Employee_ID INT PRIMARY KEY,
        First_Name VARCHAR(30),
        Last_Name VARCHAR(30),
        Hire_Date DATE,
        Phone VARCHAR(30),
        Salary INT
    );

    CREATE TABLE Kitchen_Equipment(
        Equipment_ID INT PRIMARY KEY,
        Equipment_Name VARCHAR(30),
        Purchase_Date DATE,
        Warranty_Expiry DATE,
        Status VARCHAR(30)
    );


    -- =========================================
    -- VIEWS & TRIGGERS CREATION
    -- =========================================
    
    -- MODULE 1: Supply Chain & Inventory
    CREATE TRIGGER trg_UpdateStockOnBatchReceive
    AFTER INSERT ON Batches
    BEGIN
        UPDATE Ingredients
        SET Current_stock = Current_stock + NEW.Quantity_Received
        WHERE IngredientID = NEW.IngredientID;
    END;

    CREATE VIEW vw_CurrentStockLevels AS
    SELECT
        i.IngredientID,
        i.Name AS Ingredient,
        ic.CategoryName,
        i.Current_stock,
        i.Reorder_level,
        i.unit_of_measure,
        CASE
            WHEN i.Current_stock < CAST(i.Reorder_level AS INT) THEN 'LOW'
            ELSE 'OK'
        END AS StockStatus
    FROM Ingredients i
    JOIN Ingredient_Categories ic ON i.CategoryID = ic.CategoryID;

    CREATE VIEW vw_PendingPurchaseOrders AS
    SELECT
        po.PO_ID,
        s.Name AS Supplier,
        s.Contact_person,
        po.Order_date,
        po.Exp_deleivey_date,
        po.Total_Amount,
        po.Status
    FROM Purchase_Order po
    JOIN Suppliers s ON po.SupplierID = s.SupplierID
    WHERE po.Status <> 'Delivered';

    -- MODULE 2: Product & Recipe (Core)
    CREATE TRIGGER trg_DeductIngredientOnProduction
    AFTER INSERT ON Order_Details
    BEGIN
        UPDATE Ingredients
        SET Current_stock = Current_stock - (
            (SELECT quantity_required FROM Recipes WHERE ProductID = NEW.ProductID AND IngredientID = Ingredients.IngredientID) * NEW.Quantity
        )
        WHERE IngredientID IN (SELECT IngredientID FROM Recipes WHERE ProductID = NEW.ProductID);
    END;

    CREATE VIEW vw_ProductRecipeDetail AS
    SELECT
        p.ProductID,
        p.Name AS Product,
        pc.Category_Name,
        p.Base_Price,
        i.Name AS Ingredient,
        r.quantity_required,
        i.unit_of_measure,
        i.Current_stock
    FROM Recipes r
    JOIN Products p ON r.ProductID = p.ProductID
    JOIN Product_categories pc ON p.CategoryID = pc.CategoryID
    JOIN Ingredients i ON r.IngredientID = i.IngredientID
    WHERE p.is_active = 1;

    CREATE VIEW vw_ActiveProducts AS
    SELECT
        p.ProductID,
        p.Name AS Product,
        pc.Category_Name,
        p.Description,
        p.Base_Price
    FROM Products p
    JOIN Product_categories pc ON p.CategoryID = pc.CategoryID
    WHERE p.is_active = 1;

    -- MODULE 3: Sales & Orders
    CREATE TRIGGER trg_CalcOrderFinalTotal
    AFTER INSERT ON Orders
    BEGIN
        UPDATE Orders
        SET Final_Total = NEW.Total_Amount + NEW.Tax_Amount - NEW.Discount_Amount
        WHERE Order_ID = NEW.Order_ID;
    END;

    CREATE TRIGGER trg_UpdateOrderTotalOnDetail
    AFTER INSERT ON Order_Details
    BEGIN
        UPDATE Orders
        SET Total_Amount = (SELECT SUM(Line_Total) FROM Order_Details WHERE Order_ID = NEW.Order_ID)
        WHERE Order_ID = NEW.Order_ID;
    END;

    CREATE VIEW vw_OrderSummary AS
    SELECT
        o.Order_ID,
        c.First_Name || ' ' || c.Last_Name AS Customer,
        o.Order_Date,
        o.Total_Amount,
        o.Tax_Amount,
        o.Discount_Amount,
        o.Final_Total,
        CASE WHEN p.Payment_Status = 1 THEN 'Paid' ELSE 'Unpaid' END AS PaymentStatus
    FROM Orders o
    JOIN Customers c ON o.CustomerID = c.CustomerID
    LEFT JOIN Payments p ON o.Order_ID = p.Order_ID;

    CREATE VIEW vw_TopSellingProducts AS
    SELECT
        p.Name AS Product,
        SUM(od.Quantity) AS TotalSold,
        SUM(od.Line_Total) AS TotalRevenue
    FROM Order_Details od
    JOIN Products p ON od.ProductID = p.ProductID
    GROUP BY p.ProductID, p.Name;

    -- MODULE 4: Delivery & Tracking
    CREATE TRIGGER trg_ValidateRiderAvailability
    BEFORE INSERT ON Deliveries
    WHEN EXISTS (SELECT 1 FROM Deliveries WHERE Rider_ID = NEW.Rider_ID AND Delivery_Status = 0)
    BEGIN
        SELECT RAISE(ABORT, 'Rider is already on an active delivery.');
    END;

    CREATE TRIGGER trg_SetDispatchTime
    AFTER INSERT ON Deliveries
    WHEN NEW.Dispatch_Time IS NULL OR NEW.Dispatch_Time = ''
    BEGIN
        UPDATE Deliveries 
        SET Dispatch_Time = datetime('now', 'localtime') 
        WHERE Delivery_ID = NEW.Delivery_ID;
    END;

    CREATE VIEW vw_ActiveDeliveries AS
    SELECT
        d.Delivery_ID,
        d.Order_ID,
        dr.First_Name || ' ' || dr.Last_Name AS Rider,
        dr.Vehicle_Type,
        ca.Address_Line,
        ca.City,
        d.Dispatch_Time
    FROM Deliveries d
    JOIN Delivery_Riders dr ON d.Rider_ID = dr.Rider_ID
    JOIN Customer_Addresses ca ON d.AddressID = ca.AddressID
    WHERE d.Delivery_Status = 0;

    CREATE VIEW vw_RiderPerformance AS
    SELECT
        dr.Rider_ID,
        dr.First_Name || ' ' || dr.Last_Name AS Rider,
        dr.Vehicle_Type,
        COUNT(d.Delivery_ID) AS CompletedDeliveries
    FROM Delivery_Riders dr
    LEFT JOIN Deliveries d ON dr.Rider_ID = d.Rider_ID AND d.Delivery_Status = 1
    GROUP BY dr.Rider_ID, dr.First_Name, dr.Last_Name, dr.Vehicle_Type;

    -- MODULE 5: HR & Kitchen Operations
    CREATE TRIGGER trg_PreventNegativeSalary
    BEFORE INSERT ON Employees
    WHEN NEW.Salary <= 0
    BEGIN
        SELECT RAISE(ABORT, 'Salary must be greater than zero.');
    END;

    CREATE VIEW vw_EquipmentStatusSummary AS
    SELECT
        Equipment_ID,
        Equipment_Name,
        Status,
        Purchase_Date,
        Warranty_Expiry,
        CASE
            WHEN date(Warranty_Expiry) < date('now') THEN 'Expired'
            WHEN date(Warranty_Expiry) < date('now', '+30 days') THEN 'Expiring Soon'
            ELSE 'Valid'
        END AS WarrantyStatus
    FROM Kitchen_Equipment;

    CREATE VIEW vw_SalarySummary AS
    SELECT
        COUNT(*) AS TotalEmployees,
        SUM(Salary) AS TotalMonthlyPayroll,
        AVG(Salary) AS AverageSalary,
        MAX(Salary) AS HighestSalary,
        MIN(Salary) AS LowestSalary
    FROM Employees;

    -- =========================================
    -- STATIC ENTRIES INSERTION
    -- =========================================
    INSERT INTO suppliers VALUES
    (1, 'Premium Bakers Supply', 'Tariq Mahmood', '0300-1234567', 'sales@premiumbakers.pk'),
    (2, 'Lahore Dairy Co.', 'Usman Ali', '0321-7654321', 'orders@lahoredairy.com'),
    (3, 'Sweet Packaging Hub', 'Sara Ahmed', '0333-9876543', 'hello@sweetpacks.pk'),
    (4, 'Global Spice Importers', 'Rida Khan', '0311-5554443', 'import@globalspice.com'),
    (5, 'The Cocoa Cartel', 'Bilal Raza', '0301-2223334', 'supply@cocoacartel.pk');

    INSERT INTO ingredient_categories VALUES
    (1, 'Dairy & Eggs', 'Perishable milk, butter, and eggs'),
    (2, 'Flour & Grains', 'Bulk dry baking bases'),
    (3, 'Sugars & Sweeteners', 'Caster, brown, and icing sugars'),
    (4, 'Chocolates & Cocoa', 'Couverture chocolate and cocoa powder'),
    (5, 'Leavening Agents', 'Baking soda, powder, and yeast'),
    (6, 'Nuts & Seeds', 'Walnuts, pecans, and almonds'),
    (7, 'Flavorings & Extracts', 'Vanilla, almond extract, and syrups'),
    (8, 'Packaging (Boxes)', 'Outer delivery and presentation boxes'),
    (9, 'Packaging (Decor)', 'Ribbons, stickers, and tissue paper'),
    (10, 'Fats & Oils', 'Cooking oils and shortening');

    INSERT INTO ingredients VALUES
    (1, 'All-Purpose Flour', 2, 'kg', 20, 45),
    (2, 'Caster Sugar', 3, 'kg', 15, 30),
    (3, 'Dark Brown Sugar', 3, 'kg', 10, 18),
    (4, 'Dutch Process Cocoa', 4, 'kg', 5, 12),
    (5, 'Unsalted Butter', 1, 'kg', 10, 25),
    (6, 'Free-Range Eggs', 1, 'dozen', 10, 22),
    (7, 'Dark Chocolate Chips', 4, 'kg', 8, 15),
    (8, 'Pure Vanilla Extract', 7, 'ml', 500, 1200),
    (9, 'Baking Powder', 5, 'grams', 500, 1500),
    (10, 'Baking Soda', 5, 'grams', 500, 1200),
    (11, 'Sea Salt Flakes', 7, 'grams', 200, 800),
    (12, 'Crushed Walnuts', 6, 'kg', 3, 7),
    (13, 'Milk Chocolate Chunks', 4, 'kg', 5, 10),
    (14, 'Heavy Whipping Cream', 1, 'liters', 5, 8),
    (15, 'Cream Cheese', 1, 'kg', 4, 9),
    (16, 'Chestnut Brown Bakery Box', 8, 'pcs', 100, 350),
    (17, 'Sage Green Ribbon', 9, 'meters', 50, 120),
    (18, 'Custom Logo Stickers', 9, 'pcs', 200, 850),
    (19, 'Parchment Paper Rolls', 8, 'pcs', 5, 12),
    (20, 'Vegetable Oil', 10, 'liters', 10, 20);

    INSERT INTO purchase_order VALUES
    (101, 1, '2026-03-20', '2026-03-22', 15000, 'Delivered'),
    (102, 2, '2026-03-21', '2026-03-22', 8500, 'Delivered'),
    (103, 4, '2026-03-22', '2026-03-25', 4200, 'Pending'),
    (104, 5, '2026-03-23', '2026-03-24', 22000, 'Delivered'),
    (105, 3, '2026-03-24', '2026-03-27', 12500, 'Shipped');

    INSERT INTO batches VALUES
    (1001, 1, 101, '2026-03-22', '2026-09-22', 20, 15),
    (1002, 2, 101, '2026-03-22', '2027-03-22', 15, 10),
    (1003, 3, 101, '2026-03-22', '2026-12-22', 10, 8),
    (1004, 5, 102, '2026-03-22', '2026-04-15', 10, 7),
    (1005, 6, 102, '2026-03-22', '2026-04-05', 10, 8),
    (1006, 14, 102, '2026-03-22', '2026-03-30', 5, 5),
    (1007, 15, 102, '2026-03-22', '2026-04-10', 4, 4),
    (1008, 4, 104, '2026-03-24', '2027-03-24', 10, 10),
    (1009, 7, 104, '2026-03-24', '2026-11-24', 8, 8),
    (1010, 13, 104, '2026-03-24', '2026-11-24', 5, 5),
    (1011, 8, 101, '2026-03-22', '2028-03-22', 500, 480),
    (1012, 9, 101, '2026-03-22', '2027-03-22', 500, 450),
    (1013, 10, 101, '2026-03-22', '2027-03-22', 500, 490),
    (1014, 12, 104, '2026-03-24', '2026-06-24', 3, 3),
    (1015, 20, 101, '2026-03-22', '2027-03-22', 10, 9);

    INSERT INTO product_categories VALUES
    (1, 'Signature Brownies', 'Rich, fudgy chocolate squares'),
    (2, 'Gourmet Cookies', 'Thick, soft-baked style cookies'),
    (3, 'Celebration Cakes', 'Custom frosted layer cakes');

    INSERT INTO products VALUES
    (1, 'Classic Walnut Brownie Box', 1, 'Box of 6 fudgy walnut brownies', 1200.00, 1),
    (2, 'Salted Caramel Brownie Box', 1, 'Topped with sea salt flakes', 1350.00, 1),
    (3, 'Double Chocolate Chunk Cookie', 2, 'Dark and milk chocolate mix', 250.00, 1),
    (4, 'Brown Butter Pecan Cookie', 2, 'Nutty and rich flavor profile', 280.00, 1),
    (5, 'Vanilla Bean Pound Cake', 3, 'Simple buttery classic loaf', 1500.00, 1),
    (6, 'Dark Chocolate Truffle Cake', 3, 'Dense cocoa layer cake', 2500.00, 1),
    (7, 'Nutella Stuffed Cookie', 2, 'Gooey hazelnut center', 300.00, 1),
    (8, 'Espresso Brownie Box', 1, 'Infused with dark coffee', 1300.00, 1),
    (9, 'White Choc Macadamia Cookie', 2, 'Sweet and salty crunch', 280.00, 1),
    (10, 'Red Velvet Cream Cheese Cake', 3, 'Tangy frosting on cocoa cake', 2800.00, 1),
    (11, 'Brookies Box', 1, 'Half brownie half cookie pack', 1400.00, 1),
    (12, 'Oatmeal Raisin Cookie', 2, 'Chewy spiced classic', 220.00, 1),
    (13, 'Lemon Drizzle Loaf', 3, 'Zesty and light tea cake', 1400.00, 1),
    (14, 'Peanut Butter Swirl Brownie', 1, 'Rich peanut butter marble', 1350.00, 0), 
    (15, 'Funfetti Birthday Cookie', 2, 'Loaded with rainbow sprinkles', 240.00, 1);

    INSERT INTO recipes VALUES
    (1, 1, 1, 0.40),
    (2, 1, 4, 0.25),
    (3, 1, 5, 0.30),
    (4, 1, 12, 0.15),
    (5, 2, 4, 0.25),
    (6, 2, 5, 0.30),
    (7, 2, 11, 5.00),
    (8, 3, 1, 0.35),
    (9, 3, 5, 0.20),
    (10, 3, 7, 0.15),
    (11, 3, 13, 0.15),
    (12, 4, 1, 0.30),
    (13, 4, 5, 0.25),
    (14, 4, 3, 0.20),
    (15, 4, 12, 0.15),
    (16, 5, 1, 0.30),
    (17, 5, 5, 0.25),
    (18, 5, 6, 0.33),
    (19, 5, 8, 15.00),
    (20, 6, 1, 0.20),
    (21, 6, 4, 0.40),
    (22, 6, 14, 0.50),
    (23, 6, 5, 0.20),
    (24, 7, 1, 0.35),
    (25, 7, 5, 0.25),
    (26, 7, 4, 0.10),
    (27, 7, 2, 0.20),
    (28, 8, 1, 0.30),
    (29, 8, 4, 0.30),
    (30, 8, 5, 0.30),
    (31, 8, 8, 20.00),
    (32, 9, 1, 0.35),
    (33, 9, 5, 0.25),
    (34, 9, 2, 0.20),
    (35, 9, 12, 0.15),
    (36, 10, 1, 0.30),
    (37, 10, 4, 0.10),
    (38, 10, 15, 0.40),
    (39, 10, 6, 0.25),
    (40, 11, 1, 0.35),
    (41, 11, 4, 0.15),
    (42, 11, 5, 0.25),
    (43, 11, 7, 0.15),
    (44, 12, 1, 0.35),
    (45, 12, 3, 0.25),
    (46, 12, 5, 0.20),
    (47, 12, 6, 0.16),
    (48, 13, 1, 0.30),
    (49, 13, 2, 0.25),
    (50, 13, 5, 0.25),
    (51, 13, 6, 0.33),
    (52, 14, 1, 0.30),
    (53, 14, 4, 0.25),
    (54, 14, 5, 0.25),
    (55, 14, 3, 0.20),
    (56, 15, 1, 0.40),
    (57, 15, 5, 0.25),
    (58, 15, 2, 0.25),
    (59, 15, 8, 15.00);

    INSERT INTO customers VALUES
    (1, 'Hamza', 'Tariq', '0300-1112233', 'hamza.t@email.com', '2026-01-10'),
    (2, 'Sara', 'Ahmed', '0321-4445566', 'sara.ahmed@email.com', '2026-01-12'),
    (3, 'Bilal', 'Raza', '0333-7778899', 'braza99@email.com', '2026-01-15'),
    (4, 'Ayesha', 'Gul', '0345-1239876', 'ayesha.g@email.com', '2026-01-20'),
    (5, 'Zain', 'Malik', '0311-5556667', 'zain.malik@email.com', '2026-02-01'),
    (6, 'Rida', 'Shah', '0301-9998877', 'rida.shah@email.com', '2026-02-05'),
    (7, 'Usman', 'Ali', '0322-2223344', 'usman.ali@email.com', '2026-02-10'),
    (8, 'Iqra', 'Hassan', '0332-4443322', 'iqra.h@email.com', '2026-02-14'),
    (9, 'Daniyal', 'Khan', '0302-7776655', 'd.khan@email.com', '2026-02-18'),
    (10, 'Fatima', 'Noor', '0344-8889900', 'fatima.noor@email.com', '2026-02-22'),
    (11, 'Ali', 'Zafar', '0312-3334455', 'ali.zafar@email.com', '2026-03-01'),
    (12, 'Khadija', 'Omer', '0303-6667788', 'komer@email.com', '2026-03-05'),
    (13, 'Saad', 'Mahmood', '0323-1110000', 'saad.m@email.com', '2026-03-08'),
    (14, 'Mahnoor', 'Tahir', '0334-5556677', 'mahnoor.t@email.com', '2026-03-10'),
    (15, 'Fahad', 'Mustafa', '0346-2221133', 'fahad.m@email.com', '2026-03-12'),
    (16, 'Sana', 'Javed', '0313-8887766', 'sana.j@email.com', '2026-03-15'),
    (17, 'Omer', 'Farooq', '0304-4445566', 'omer.f@email.com', '2026-03-18'),
    (18, 'Nida', 'Yasir', '0324-9990011', 'nida.y@email.com', '2026-03-20'),
    (19, 'Taha', 'Qureshi', '0335-3332211', 'taha.q@email.com', '2026-03-22'),
    (20, 'Hira', 'Mani', '0347-6665544', 'hira.m@email.com', '2026-03-24');

    INSERT INTO customer_addresses VALUES
    (1, 1, 'House 45, Dha Phase 6', 'Lahore', 'Home', 1),
    (2, 2, 'Apt 12, Askari 11', 'Lahore', 'Home', 1),
    (3, 3, 'Office 3, Arfa Tower', 'Lahore', 'Work', 1),
    (4, 4, 'House 88, Johar Town', 'Lahore', 'Home', 1),
    (5, 5, 'Plaza 5, Gulberg III', 'Lahore', 'Work', 1),
    (6, 6, 'House 12, Model Town', 'Lahore', 'Home', 1),
    (7, 7, 'Apt 4B, Bahria Town', 'Lahore', 'Home', 1),
    (8, 8, 'Shop 9, Liberty Market', 'Lahore', 'Work', 1),
    (9, 9, 'House 55, Wapda Town', 'Lahore', 'Home', 1),
    (10, 10, 'House 2, Dha Phase 5', 'Lahore', 'Home', 1),
    (11, 11, 'Office 1, MM Alam Road', 'Lahore', 'Work', 1),
    (12, 12, 'House 34, Cantt', 'Lahore', 'Home', 1),
    (13, 13, 'Apt 9, Askari 10', 'Lahore', 'Home', 1),
    (14, 14, 'House 77, Iqbal Town', 'Lahore', 'Home', 1),
    (15, 15, 'Plaza 2, Faisal Town', 'Lahore', 'Work', 1),
    (16, 16, 'House 19, Garden Town', 'Lahore', 'Home', 1),
    (17, 17, 'House 8, Dha Phase 8', 'Lahore', 'Home', 1),
    (18, 18, 'Office 7, Jail Road', 'Lahore', 'Work', 1),
    (19, 19, 'House 90, Township', 'Lahore', 'Home', 1),
    (20, 20, 'Apt 3A, Valencia Town', 'Lahore', 'Home', 1);

    INSERT INTO orders VALUES
    (101, 1, '2026-03-20', 1200.00, 60.00, 0.00, 1260.00),
    (102, 2, '2026-03-20', 2500.00, 125.00, 0.00, 2625.00),
    (103, 3, '2026-03-20', 1350.00, 67.50, 0.00, 1417.50),
    (104, 4, '2026-03-21', 500.00, 25.00, 0.00, 525.00),
    (105, 5, '2026-03-21', 1500.00, 75.00, 100.00, 1475.00), 
    (106, 6, '2026-03-21', 2800.00, 140.00, 0.00, 2940.00),
    (107, 7, '2026-03-22', 1200.00, 60.00, 0.00, 1260.00),
    (108, 8, '2026-03-22', 560.00, 28.00, 0.00, 588.00),
    (109, 9, '2026-03-22', 1400.00, 70.00, 0.00, 1470.00),
    (110, 10, '2026-03-22', 300.00, 15.00, 0.00, 315.00),
    (111, 11, '2026-03-23', 2500.00, 125.00, 0.00, 2625.00),
    (112, 12, '2026-03-23', 1300.00, 65.00, 0.00, 1365.00),
    (113, 13, '2026-03-23', 1350.00, 67.50, 0.00, 1417.50),
    (114, 14, '2026-03-24', 440.00, 22.00, 0.00, 462.00),
    (115, 15, '2026-03-24', 1200.00, 60.00, 0.00, 1260.00),
    (116, 16, '2026-03-24', 2800.00, 140.00, 200.00, 2740.00),
    (117, 1, '2026-03-24', 1400.00, 70.00, 0.00, 1470.00),  
    (118, 17, '2026-03-25', 240.00, 12.00, 0.00, 252.00),
    (119, 18, '2026-03-25', 1500.00, 75.00, 0.00, 1575.00),
    (120, 19, '2026-03-25', 500.00, 25.00, 0.00, 525.00),
    (121, 2, '2026-03-25', 1350.00, 67.50, 0.00, 1417.50),  
    (122, 20, '2026-03-25', 280.00, 14.00, 0.00, 294.00),
    (123, 3, '2026-03-26', 1400.00, 70.00, 0.00, 1470.00),  
    (124, 4, '2026-03-26', 1200.00, 60.00, 0.00, 1260.00),
    (125, 5, '2026-03-26', 2500.00, 125.00, 0.00, 2625.00),
    (126, 6, '2026-03-26', 300.00, 15.00, 0.00, 315.00),
    (127, 7, '2026-03-26', 1300.00, 65.00, 0.00, 1365.00),
    (128, 8, '2026-03-26', 1350.00, 67.50, 0.00, 1417.50),
    (129, 9, '2026-03-26', 560.00, 28.00, 0.00, 588.00),
    (130, 10, '2026-03-26', 2800.00, 140.00, 0.00, 2940.00);

    INSERT INTO order_details VALUES
    (1, 101, 1, 1, 1200.00, 1200.00),
    (2, 102, 6, 1, 2500.00, 2500.00),
    (3, 103, 2, 1, 1350.00, 1350.00),
    (4, 104, 3, 2, 250.00, 500.00),
    (5, 105, 5, 1, 1500.00, 1500.00),
    (6, 106, 10, 1, 2800.00, 2800.00),
    (7, 107, 1, 1, 1200.00, 1200.00), 
    (8, 108, 4, 2, 280.00, 560.00),
    (9, 109, 11, 1, 1400.00, 1400.00),
    (10, 110, 7, 1, 300.00, 300.00),
    (11, 111, 6, 1, 2500.00, 2500.00),
    (12, 112, 8, 1, 1300.00, 1300.00),
    (13, 113, 14, 1, 1350.00, 1350.00),
    (14, 114, 12, 2, 220.00, 440.00),
    (15, 115, 1, 1, 1200.00, 1200.00),
    (16, 116, 10, 1, 2800.00, 2800.00),
    (17, 117, 13, 1, 1400.00, 1400.00),
    (18, 118, 15, 1, 240.00, 240.00),
    (19, 119, 5, 1, 1500.00, 1500.00),
    (20, 120, 3, 2, 250.00, 500.00),
    (21, 121, 2, 1, 1350.00, 1350.00),
    (22, 122, 9, 1, 280.00, 280.00),
    (23, 123, 11, 1, 1400.00, 1400.00),
    (24, 124, 1, 1, 1200.00, 1200.00),
    (25, 125, 6, 1, 2500.00, 2500.00),
    (26, 126, 7, 1, 300.00, 300.00),
    (27, 127, 8, 1, 1300.00, 1300.00),
    (28, 128, 14, 1, 1350.00, 1350.00),
    (29, 129, 4, 2, 280.00, 560.00),
    (30, 130, 10, 1, 2800.00, 2800.00);

    INSERT INTO payments VALUES
    (1, 101, '2026-03-20', 1260.00, 1),
    (2, 102, '2026-03-20', 2625.00, 1),
    (3, 103, '2026-03-20', 1417.50, 1),
    (4, 104, '2026-03-21', 525.00, 1),
    (5, 105, '2026-03-21', 1475.00, 1),
    (6, 106, '2026-03-21', 2940.00, 1),
    (7, 107, '2026-03-22', 1260.00, 1),
    (8, 108, '2026-03-22', 588.00, 1),
    (9, 109, '2026-03-22', 1470.00, 1),
    (10, 110, '2026-03-22', 315.00, 1),
    (11, 111, '2026-03-23', 2625.00, 1),
    (12, 112, '2026-03-23', 1365.00, 1),
    (13, 113, '2026-03-23', 1417.50, 1),
    (14, 114, '2026-03-24', 462.00, 1),
    (15, 115, '2026-03-24', 1260.00, 1),
    (16, 116, '2026-03-24', 2740.00, 1),
    (17, 117, '2026-03-24', 1470.00, 1),
    (18, 118, '2026-03-25', 252.00, 1),
    (19, 119, '2026-03-25', 1575.00, 1),
    (20, 120, '2026-03-25', 525.00, 1),
    (21, 121, '2026-03-25', 1417.50, 1),
    (22, 122, '2026-03-25', 294.00, 1),
    (23, 123, '2026-03-26', 1470.00, 1),
    (24, 124, '2026-03-26', 1260.00, 1),
    (25, 125, '2026-03-26', 2625.00, 1),
    (26, 126, '2026-03-26', 315.00, 1),
    (27, 127, '2026-03-26', 1365.00, 1),
    (28, 128, '2026-03-26', 1417.50, 1),
    (29, 129, '2026-03-26', 588.00, 1),
    (30, 130, '2026-03-26', 2940.00, 1);

    INSERT INTO delivery_riders VALUES
    (1, 'Kamran', 'Baqir', '0300-1110001', 'Honda CD 70'),
    (2, 'Shoaib', 'Tariq', '0300-1110002', 'Suzuki GS 150'),
    (3, 'Babar', 'Ali', '0300-1110003', 'Honda CG 125'),
    (4, 'Shaheen', 'Shah', '0300-1110004', 'Yamaha YBR 125'),
    (5, 'Fakhar', 'Zaman', '0300-1110005', 'Honda Pridor');

    INSERT INTO deliveries VALUES
    (1, 101, 1, 1, '2026-03-20 10:00:00', '2026-03-20 10:45:00', 1),
    (2, 102, 2, 2, '2026-03-20 12:30:00', '2026-03-20 13:10:00', 1),
    (3, 103, 3, 3, '2026-03-20 15:15:00', '2026-03-20 15:55:00', 1),
    (4, 104, 4, 4, '2026-03-21 09:30:00', '2026-03-21 10:15:00', 1),
    (5, 105, 5, 5, '2026-03-21 11:45:00', '2026-03-21 12:20:00', 1),
    (6, 106, 1, 6, '2026-03-21 16:00:00', '2026-03-21 16:35:00', 1),
    (7, 107, 2, 7, '2026-03-22 10:20:00', '2026-03-22 11:00:00', 1),
    (8, 108, 3, 8, '2026-03-22 13:10:00', '2026-03-22 13:45:00', 1),
    (9, 109, 4, 9, '2026-03-22 15:30:00', '2026-03-22 16:10:00', 1),
    (10, 110, 5, 10, '2026-03-22 18:00:00', '2026-03-22 18:30:00', 1),
    (11, 111, 1, 11, '2026-03-23 09:15:00', '2026-03-23 09:50:00', 1),
    (12, 112, 2, 12, '2026-03-23 12:00:00', '2026-03-23 12:40:00', 1),
    (13, 113, 3, 13, '2026-03-23 14:45:00', '2026-03-23 15:25:00', 1),
    (14, 114, 4, 14, '2026-03-24 10:00:00', '2026-03-24 10:35:00', 1),
    (15, 115, 5, 15, '2026-03-24 11:30:00', '2026-03-24 12:15:00', 1),
    (16, 116, 1, 16, '2026-03-24 14:20:00', '2026-03-24 15:00:00', 1),
    (17, 117, 2, 1, '2026-03-24 17:10:00', '2026-03-24 17:45:00', 1), 
    (18, 118, 3, 17, '2026-03-25 09:05:00', '2026-03-25 09:40:00', 1),
    (19, 119, 4, 18, '2026-03-25 11:50:00', '2026-03-25 12:30:00', 1),
    (20, 120, 5, 19, '2026-03-25 13:40:00', '2026-03-25 14:20:00', 1),
    (21, 121, 1, 2, '2026-03-25 16:15:00', '2026-03-25 16:55:00', 1), 
    (22, 122, 2, 20, '2026-03-25 18:30:00', '2026-03-25 19:10:00', 1),
    (23, 123, 3, 3, '2026-03-26 10:00:00', '2026-03-26 10:45:00', 1), 
    (24, 124, 4, 4, '2026-03-26 11:20:00', '2026-03-26 12:00:00', 1),
    (25, 125, 5, 5, '2026-03-26 13:10:00', '2026-03-26 13:50:00', 1),
    (26, 126, 1, 6, '2026-03-26 14:45:00', '2026-03-26 15:20:00', 1),
    (27, 127, 2, 7, '2026-03-26 16:00:00', '2026-03-26 16:40:00', 1),
    (28, 128, 3, 8, '2026-03-26 17:30:00', null, 0), 
    (29, 129, 4, 9, '2026-03-26 18:15:00', null, 0), 
    (30, 130, 5, 10, '2026-03-26 18:45:00', null, 0); 

    INSERT INTO Employees VALUES
    (1,'Ali','Khan','2021-03-15','03001234567',45000),
    (2,'Ahmed','Raza','2020-07-10','03111234567',52000),
    (3,'Usman','Ali','2022-01-05','03221234567',40000),
    (4,'Hamza','Sheikh','2019-11-20','03331234567',60000),
    (5,'Bilal','Hussain','2023-02-18','03441234567',38000),
    (6,'Saad','Malik','2021-06-25','03051234567',47000),
    (7,'Zain','Iqbal','2020-09-30','03161234567',51000),
    (8,'Fahad','Mirza','2018-04-12','03271234567',65000),
    (9,'Hassan','Rauf','2022-08-08','03381234567',42000),
    (10,'Tariq','Mehmood','2019-01-28','03491234567',58000),
    (11,'Imran','Aslam','2021-12-14','03021234567',46000),
    (12,'Noman','Shah','2023-03-03','03131234567',39000),
    (13,'Kashif','Abbasi','2020-05-19','03241234567',53000),
    (14,'Rizwan','Qureshi','2018-10-22','03351234567',67000),
    (15,'Yasir','Latif','2022-06-11','03461234567',41000);

    INSERT INTO Kitchen_Equipment VALUES
    (1,'Oven','2020-02-15','2025-02-15','Working'),
    (2,'Refrigerator','2019-06-10','2024-06-10','Working'),
    (3,'Microwave','2021-01-20','2026-01-20','Working'),
    (4,'Blender','2022-03-05','2025-03-05','Under Repair'),
    (5,'Dishwasher','2018-11-25','2023-11-25','Not Working'),
    (6,'Toaster','2020-07-14','2024-07-14','Working'),
    (7,'Freezer','2019-09-09','2024-09-09','Working'),
    (8,'Coffee Maker','2021-12-01','2025-12-01','Working'),
    (9,'Juicer','2022-05-18','2026-05-18','Working'),
    (10,'Gas Stove','2017-08-30','2022-08-30','Not Working'),
    (11,'Electric Kettle','2023-01-10','2026-01-10','Working'),
    (12,'Grill Machine','2020-04-22','2025-04-22','Under Repair'),
    (13,'Rice Cooker','2021-10-17','2025-10-17','Working'),
    (14,'Deep Fryer','2019-12-12','2024-12-12','Working'),
    (15,'Food Processor','2022-07-07','2026-07-07','Working');
    """

    cursor.executescript(sql_script)
    conn.commit()
    conn.close()
    print("Success: bakeshop.db successfully created and populated for Streamlit deployment!")

if __name__ == "__main__":
    create_database()