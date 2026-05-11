-----.SQL FILE INDEX-----
--Line 13: Database Creation
--Line 16: Tables Creation
--Line 178: Static Entries Insertion
--Line 634: View All Tables
--Line 660: Modify Tables (Make/Remove Entries)



-----END OF INDEX


create database Project 
use  Project

-----module 1(supply chain & inventory)----
create table Suppliers(
SupplierID int primary key,
Name Varchar(30),
Contact_person Varchar(30),
Phone Varchar(30),
Email_address  varchar(30))

create table Ingredient_Categories(
CategoryID int primary key,
CategoryName Varchar(50),
Description Varchar(50)) 

create table Ingredients(
IngredientID int primary key,
Name Varchar(30),
CategoryID int,
unit_of_measure varchar(30),
Reorder_level varchar(30),
Current_stock int,
foreign key (CategoryID) references Ingredient_Categories(CategoryID))
 
create table Purchase_Order(
PO_ID int primary key,
SupplierID int,
Order_date date,
Exp_deleivey_date date,
Total_Amount int,
Status varchar(20),
foreign key (SupplierID) references Suppliers(SupplierID))

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
CREATE TRIGGER trg_UpdateStockOnBatchReceive
ON Batches
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE i
    SET i.Current_stock = i.Current_stock + ins.Quantity_Received
    FROM Ingredients i
    INNER JOIN inserted ins ON i.IngredientID = ins.IngredientID;
END;


CREATE PROCEDURE sp_PlacePurchaseOrder
    @PO_ID       INT,
    @SupplierID  INT,
    @OrderDate   DATE,
    @ExpDate     DATE,
    @TotalAmount INT,
    @Status      VARCHAR(20)
AS
BEGIN
    SET NOCOUNT ON;
    IF NOT EXISTS (SELECT 1 FROM Suppliers WHERE SupplierID = @SupplierID)
    BEGIN
        RAISERROR('Supplier not found.', 16, 1);
        RETURN;
    END
    INSERT INTO Purchase_Order (PO_ID, SupplierID, Order_date,
        Exp_deleivey_date, Total_Amount, Status)
    VALUES (@PO_ID, @SupplierID, @OrderDate, @ExpDate, @TotalAmount, @Status);
END;

CREATE PROCEDURE sp_ReceiveBatch
    @BatchID      INT,
    @IngredientID INT,
    @PO_ID        INT,
    @ReceiveDate  DATE,
    @ExpiryDate   DATE,
    @QtyReceived  INT
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO Batches (BatchID, IngredientID, PO_ID, Receive_date,
        Expiry_date, Quantity_Received, Remaining_Quantity)
    VALUES (@BatchID, @IngredientID, @PO_ID, @ReceiveDate,
        @ExpiryDate, @QtyReceived, @QtyReceived);
END;

CREATE VIEW vw_CurrentStockLevels AS
SELECT
    i.IngredientID,
    i.Name              AS Ingredient,
    ic.CategoryName,
    i.Current_stock,
    i.Reorder_level,
    i.unit_of_measure,
    CASE
        WHEN i.Current_stock < CAST(i.Reorder_level AS INT)
        THEN 'LOW'
        ELSE 'OK'
    END                 AS StockStatus
FROM Ingredients i
JOIN Ingredient_Categories ic ON i.CategoryID = ic.CategoryID;

CREATE VIEW vw_PendingPurchaseOrders AS
SELECT
    po.PO_ID,
    s.Name              AS Supplier,
    s.Contact_person,
    po.Order_date,
    po.Exp_deleivey_date,
    po.Total_Amount,
    po.Status
FROM Purchase_Order po
JOIN Suppliers s ON po.SupplierID = s.SupplierID
WHERE po.Status <> 'Delivered';


----module 2 Product & recipe(core)---
create table Product_categories( 
    CategoryID INT primary key,
	Category_Name varchar(50),
	Description varchar(50))

create table Products (
ProductID int primary key,
Name varchar(30),
CategoryID INT,
Description varchar(30),
Base_Price decimal(8,2),
is_active int,
foreign key (CategoryID) references Product_categories(CategoryID))

create table Recipes (
RecipeID Int primary key,
ProductID int,
IngredientID int,
foreign key (ProductID) references Products(ProductID),
foreign key (IngredientID) references Ingredients(IngredientID))

alter table recipes
add quantity_required decimal(8,2);

CREATE TRIGGER trg_DeductIngredientOnProduction
ON Order_Details
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE i
    SET i.Current_stock = i.Current_stock
        - (r.quantity_required * ins.Quantity)
    FROM Ingredients i
    JOIN Recipes r  ON i.IngredientID = r.IngredientID
    JOIN inserted ins ON r.ProductID  = ins.ProductID;
END;

CREATE PROCEDURE sp_AddRecipeIngredient
    @RecipeID     INT,
    @ProductID    INT,
    @IngredientID INT,
    @QtyRequired  DECIMAL(8,2)
AS
BEGIN
    SET NOCOUNT ON;
    IF NOT EXISTS (SELECT 1 FROM Products WHERE ProductID = @ProductID)
    BEGIN
        RAISERROR('Product not found.', 16, 1); RETURN;
    END
    IF NOT EXISTS (SELECT 1 FROM Ingredients WHERE IngredientID = @IngredientID)
    BEGIN
        RAISERROR('Ingredient not found.', 16, 1); RETURN;
    END
    INSERT INTO Recipes (RecipeID, ProductID, IngredientID, quantity_required)
    VALUES (@RecipeID, @ProductID, @IngredientID, @QtyRequired);
END;

CREATE PROCEDURE sp_CheckProductFeasibility
    @ProductID INT,
    @Quantity  INT
AS
BEGIN
    SET NOCOUNT ON;
    SELECT
        i.Name                              AS Ingredient,
        r.quantity_required * @Quantity     AS Needed,
        i.Current_stock                     AS Available,
        CASE
            WHEN i.Current_stock >= r.quantity_required * @Quantity
            THEN 'Feasible'
            ELSE 'Insufficient'
        END                                 AS Status
    FROM Recipes r
    JOIN Ingredients i ON r.IngredientID = i.IngredientID
    WHERE r.ProductID = @ProductID;
END;

CREATE VIEW vw_ProductRecipeDetail AS
SELECT
    p.ProductID,
    p.Name              AS Product,
    pc.Category_Name,
    p.Base_Price,
    i.Name              AS Ingredient,
    r.quantity_required,
    i.unit_of_measure,
    i.Current_stock
FROM Recipes r
JOIN Products p           ON r.ProductID    = p.ProductID
JOIN Product_categories pc ON p.CategoryID  = pc.CategoryID
JOIN Ingredients i        ON r.IngredientID = i.IngredientID
WHERE p.is_active = 1;

CREATE VIEW vw_ActiveProducts AS
SELECT
    p.ProductID,
    p.Name              AS Product,
    pc.Category_Name,
    p.Description,
    p.Base_Price
FROM Products p
JOIN Product_categories pc ON p.CategoryID = pc.CategoryID
WHERE p.is_active = 1;

--module 3 Sales & Orders---

create table customers (
CustomerID int primary key,
First_Name varchar(30),
Last_Name  varchar(30),
Phone varchar(30),
Email varchar(30),
Registration_Date date )

create table Customer_Addresses(
AddressID int primary key,
CustomerID int ,
Address_Line varchar(30),
City varchar(30),
Address_Type  varchar (30),
Is_Default bit,
foreign key (CustomerID) references customers(CustomerID))

create table Orders ( --(Main Invoice Table)---
Order_ID int primary key,
CustomerID int,
Order_Date date,
Total_Amount decimal(8,2),
Tax_Amount decimal(8,2),
Discount_Amount decimal(8,2),
Final_Total  decimal(8,2)
foreign key (CustomerID) references customers(CustomerID))

create table Order_Details(
Order_Detail_ID int primary key,
Order_ID int,
ProductID int ,
Quantity int,
Unit_Price decimal(8,3),
Line_Total decimal(8,3),
foreign key (Order_ID) references Orders(Order_ID),
foreign key (ProductID) references Products(ProductID))

create table payments (
Payment_ID int primary key,
Order_ID int ,
Payment_Date date,
Amount_Paid int,
Payment_Status bit
foreign key (Order_ID) references Orders(Order_ID))

----triggers
CREATE TRIGGER trg_CalcOrderFinalTotal
ON Orders
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE o
    SET o.Final_Total = o.Total_Amount + o.Tax_Amount - o.Discount_Amount
    FROM Orders o
    JOIN inserted ins ON o.Order_ID = ins.Order_ID;
END;

CREATE TRIGGER trg_UpdateOrderTotalOnDetail
ON Order_Details
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE o
    SET o.Total_Amount = (
        SELECT SUM(od.Line_Total)
        FROM Order_Details od
        WHERE od.Order_ID = o.Order_ID
    )
    FROM Orders o
    JOIN inserted ins ON o.Order_ID = ins.Order_ID;
END;
------PROCEDURE
CREATE PROCEDURE sp_PlaceOrder
    @Order_ID        INT,
    @CustomerID      INT,
    @Order_Date      DATE,
    @Tax_Amount      DECIMAL(8,2),
    @Discount_Amount DECIMAL(8,2)
AS
BEGIN
    SET NOCOUNT ON;
    IF NOT EXISTS (SELECT 1 FROM Customers WHERE CustomerID = @CustomerID)
    BEGIN
        RAISERROR('Customer not found.', 16, 1); RETURN;
    END
    INSERT INTO Orders (Order_ID, CustomerID, Order_Date,
        Total_Amount, Tax_Amount, Discount_Amount, Final_Total)
    VALUES (@Order_ID, @CustomerID, @Order_Date,
        0, @Tax_Amount, @Discount_Amount, 0);
END;

CREATE PROCEDURE sp_ProcessPayment
    @PaymentID  INT,
    @OrderID    INT,
    @PayDate    DATE,
    @AmountPaid INT
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @Expected DECIMAL(8,2);
    SELECT @Expected = Final_Total FROM Orders WHERE Order_ID = @OrderID;

    IF @AmountPaid < @Expected
    BEGIN
        RAISERROR('Underpayment: amount is less than order total.', 16, 1);
        RETURN;
    END
    INSERT INTO Payments (Payment_ID, Order_ID, Payment_Date, Amount_Paid, Payment_Status)
    VALUES (@PaymentID, @OrderID, @PayDate, @AmountPaid, 1);
END;

---views

CREATE VIEW vw_OrderSummary AS
SELECT
    o.Order_ID,
    c.First_Name + ' ' + c.Last_Name   AS Customer,
    o.Order_Date,
    o.Total_Amount,
    o.Tax_Amount,
    o.Discount_Amount,
    o.Final_Total,
    CASE WHEN p.Payment_Status = 1
         THEN 'Paid' ELSE 'Unpaid' END  AS PaymentStatus
FROM Orders o
JOIN Customers c  ON o.CustomerID = c.CustomerID
LEFT JOIN Payments p ON o.Order_ID = p.Order_ID;

CREATE VIEW vw_TopSellingProducts AS
SELECT
    p.Name              AS Product,
    SUM(od.Quantity)    AS TotalSold,
    SUM(od.Line_Total)  AS TotalRevenue
FROM Order_Details od
JOIN Products p ON od.ProductID = p.ProductID
GROUP BY p.ProductID, p.Name;



--module 4 Delivery & Tracking--

create table Delivery_Riders(
Rider_ID int primary key,
First_Name varchar(30),
Last_Name varchar(30),
Phone varchar(30),
Vehicle_Type varchar(30))

create table Deliveries(
Delivery_ID int primary key,
Order_ID int,
Rider_ID int,
AddressID int,
Dispatch_Time varchar(60),
Delivery_Time varchar(60),
Delivery_Status bit,
foreign key (Order_ID) references Orders(Order_ID),
foreign key (Rider_ID) references Delivery_Riders(Rider_ID),
foreign key (AddressID) references Customer_Addresses(AddressID))

CREATE TRIGGER trg_ValidateRiderAvailability
ON Deliveries
INSTEAD OF INSERT
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (
        SELECT 1 FROM Deliveries d
        JOIN inserted ins ON d.Rider_ID = ins.Rider_ID
        WHERE d.Delivery_Status = 0
    )
    BEGIN
        RAISERROR('Rider is already on an active delivery.', 16, 1);
        RETURN;
    END
    INSERT INTO Deliveries
    SELECT * FROM inserted;
END;

CREATE TRIGGER trg_SetDispatchTime
ON Deliveries
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE d
    SET d.Dispatch_Time = CONVERT(VARCHAR(60), GETDATE(), 120)
    FROM Deliveries d
    JOIN inserted ins ON d.Delivery_ID = ins.Delivery_ID
    WHERE d.Dispatch_Time IS NULL OR d.Dispatch_Time = '';
END;

CREATE PROCEDURE sp_AssignDelivery
    @DeliveryID INT,
    @OrderID    INT,
    @RiderID    INT,
    @AddressID  INT
AS
BEGIN
    SET NOCOUNT ON;
    IF NOT EXISTS (SELECT 1 FROM Orders WHERE Order_ID = @OrderID)
    BEGIN
        RAISERROR('Order not found.', 16, 1); RETURN;
    END
    IF NOT EXISTS (SELECT 1 FROM Delivery_Riders WHERE Rider_ID = @RiderID)
    BEGIN
        RAISERROR('Rider not found.', 16, 1); RETURN;
    END
    INSERT INTO Deliveries
        (Delivery_ID, Order_ID, Rider_ID, AddressID,
         Dispatch_Time, Delivery_Time, Delivery_Status)
    VALUES
        (@DeliveryID, @OrderID, @RiderID, @AddressID,
         CONVERT(VARCHAR(60), GETDATE(), 120), NULL, 0);
END;

CREATE PROCEDURE sp_CompleteDelivery
    @DeliveryID INT
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE Deliveries
    SET Delivery_Status = 1,
        Delivery_Time   = CONVERT(VARCHAR(60), GETDATE(), 120)
    WHERE Delivery_ID = @DeliveryID;
END;


CREATE VIEW vw_ActiveDeliveries AS
SELECT
    d.Delivery_ID,
    d.Order_ID,
    dr.First_Name + ' ' + dr.Last_Name  AS Rider,
    dr.Vehicle_Type,
    ca.Address_Line,
    ca.City,
    d.Dispatch_Time
FROM Deliveries d
JOIN Delivery_Riders dr    ON d.Rider_ID  = dr.Rider_ID
JOIN Customer_Addresses ca ON d.AddressID = ca.AddressID
WHERE d.Delivery_Status = 0;

CREATE VIEW vw_RiderPerformance AS
SELECT
    dr.Rider_ID,
    dr.First_Name + ' ' + dr.Last_Name  AS Rider,
    dr.Vehicle_Type,
    COUNT(d.Delivery_ID)                AS CompletedDeliveries
FROM Delivery_Riders dr
LEFT JOIN Deliveries d ON dr.Rider_ID = d.Rider_ID
    AND d.Delivery_Status = 1
GROUP BY dr.Rider_ID, dr.First_Name, dr.Last_Name, dr.Vehicle_Type;

---module 5 HR & Kitchen Operations----

create table Employees(
Employee_ID int primary key,
First_Name varchar(30),
Last_Name varchar(30),
Hire
._Date date,
Phone varchar(30),
Salary int)

create table Kitchen_Equipment(
Equipment_ID int primary key,
Equipment_Name varchar(30),
Purchase_Date date,
Warranty_Expiry date,
Status varchar(30))

CREATE TRIGGER trg_PreventNegativeSalary
ON Employees
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (SELECT 1 FROM inserted WHERE Salary <= 0)
    BEGIN
        RAISERROR('Salary must be greater than zero.', 16, 1);
        ROLLBACK TRANSACTION;
        RETURN;
    END
END;

CREATE PROCEDURE sp_HireEmployee
    @EmpID     INT,
    @FirstName VARCHAR(30),
    @LastName  VARCHAR(30),
    @Phone     VARCHAR(30),
    @Salary    INT
AS
BEGIN
    SET NOCOUNT ON;
    IF @Salary <= 0
    BEGIN
        RAISERROR('Salary must be a positive value.', 16, 1); RETURN;
    END
    INSERT INTO Employees
        (Employee_ID, First_Name, Last_Name, Hire_Date, Phone, Salary)
    VALUES
        (@EmpID, @FirstName, @LastName, GETDATE(), @Phone, @Salary);
END;

CREATE PROCEDURE sp_UpdateEquipmentStatus
    @EquipmentID INT,
    @NewStatus   VARCHAR(30)
AS
BEGIN
    SET NOCOUNT ON;
    IF @NewStatus NOT IN ('Working', 'Under Repair', 'Not Working')
    BEGIN
        RAISERROR('Invalid status. Use: Working, Under Repair, Not Working.', 16, 1);
        RETURN;
    END
    UPDATE Kitchen_Equipment
    SET Status = @NewStatus
    WHERE Equipment_ID = @EquipmentID;
END;

CREATE VIEW vw_EquipmentStatusSummary AS
SELECT
    Equipment_ID,
    Equipment_Name,
    Status,
    Purchase_Date,
    Warranty_Expiry,
    CASE
        WHEN Warranty_Expiry < GETDATE()                    THEN 'Expired'
        WHEN Warranty_Expiry < DATEADD(DAY, 30, GETDATE())  THEN 'Expiring Soon'
        ELSE 'Valid'
    END AS WarrantyStatus
FROM Kitchen_Equipment;

CREATE VIEW vw_SalarySummary AS
SELECT
    COUNT(*)      AS TotalEmployees,
    SUM(Salary)   AS TotalMonthlyPayroll,
    AVG(Salary)   AS AverageSalary,
    MAX(Salary)   AS HighestSalary,
    MIN(Salary)   AS LowestSalary
FROM Employees;

--ENTRIES INSERTION--
--MOD 1--


insert into suppliers values
(1, 'Premium Bakers Supply', 'Tariq Mahmood', '0300-1234567', 'sales@premiumbakers.pk'),
(2, 'Lahore Dairy Co.', 'Usman Ali', '0321-7654321', 'orders@lahoredairy.com'),
(3, 'Sweet Packaging Hub', 'Sara Ahmed', '0333-9876543', 'hello@sweetpacks.pk'),
(4, 'Global Spice Importers', 'Rida Khan', '0311-5554443', 'import@globalspice.com'),
(5, 'The Cocoa Cartel', 'Bilal Raza', '0301-2223334', 'supply@cocoacartel.pk');


insert into ingredient_categories values
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


insert into ingredients values
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


insert into purchase_order values
(101, 1, '2026-03-20', '2026-03-22', 15000, 'Delivered'),
(102, 2, '2026-03-21', '2026-03-22', 8500, 'Delivered'),
(103, 4, '2026-03-22', '2026-03-25', 4200, 'Pending'),
(104, 5, '2026-03-23', '2026-03-24', 22000, 'Delivered'),
(105, 3, '2026-03-24', '2026-03-27', 12500, 'Shipped');


insert into batches values
(1001, 1, 101, '2026-03-22', '2026-09-22', 20, 15),    -- Flour
(1002, 2, 101, '2026-03-22', '2027-03-22', 15, 10),    -- Caster Sugar
(1003, 3, 101, '2026-03-22', '2026-12-22', 10, 8),     -- Brown Sugar
(1004, 5, 102, '2026-03-22', '2026-04-15', 10, 7),     -- Butter
(1005, 6, 102, '2026-03-22', '2026-04-05', 10, 8),     -- Eggs
(1006, 14, 102, '2026-03-22', '2026-03-30', 5, 5),     -- Heavy Cream
(1007, 15, 102, '2026-03-22', '2026-04-10', 4, 4),     -- Cream Cheese
(1008, 4, 104, '2026-03-24', '2027-03-24', 10, 10),    -- Cocoa Powder
(1009, 7, 104, '2026-03-24', '2026-11-24', 8, 8),      -- Dark Choc Chips
(1010, 13, 104, '2026-03-24', '2026-11-24', 5, 5),     -- Milk Choc Chunks
(1011, 8, 101, '2026-03-22', '2028-03-22', 500, 480),  -- Vanilla
(1012, 9, 101, '2026-03-22', '2027-03-22', 500, 450),  -- Baking Powder
(1013, 10, 101, '2026-03-22', '2027-03-22', 500, 490), -- Baking Soda
(1014, 12, 104, '2026-03-24', '2026-06-24', 3, 3),     -- Walnuts
(1015, 20, 101, '2026-03-22', '2027-03-22', 10, 9);    -- Veg Oil



--MOD 2--


insert into product_categories values
(1, 'Signature Brownies', 'Rich, fudgy chocolate squares'),
(2, 'Gourmet Cookies', 'Thick, soft-baked style cookies'),
(3, 'Celebration Cakes', 'Custom frosted layer cakes');


insert into products values
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
(14, 'Peanut Butter Swirl Brownie', 1, 'Rich peanut butter marble', 1350.00, 0), -- 0 means currently out of stock/inactive
(15, 'Funfetti Birthday Cookie', 2, 'Loaded with rainbow sprinkles', 240.00, 1);



insert into recipes values
-- Product 1: Classic Walnut Brownie Box
(1, 1, 1, 0.40),  -- Flour (kg)
(2, 1, 4, 0.25),  -- Cocoa (kg)
(3, 1, 5, 0.30),  -- Butter (kg)
(4, 1, 12, 0.15), -- Walnuts (kg)

-- Product 2: Salted Caramel Brownie Box
(5, 2, 4, 0.25),  -- Cocoa (kg)
(6, 2, 5, 0.30),  -- Butter (kg)
(7, 2, 11, 5.00), -- Sea Salt (g)

-- Product 3: Double Chocolate Chunk Cookie
(8, 3, 1, 0.35),  -- Flour (kg)
(9, 3, 5, 0.20),  -- Butter (kg)
(10, 3, 7, 0.15), -- Dark Choc Chips (kg)
(11, 3, 13, 0.15),-- Milk Choc Chunks (kg)

-- Product 4: Brown Butter Pecan Cookie (Mapped with Walnuts)
(12, 4, 1, 0.30), -- Flour (kg)
(13, 4, 5, 0.25), -- Butter (kg)
(14, 4, 3, 0.20), -- Brown Sugar (kg)
(15, 4, 12, 0.15),-- Walnuts (kg)

-- Product 5: Vanilla Bean Pound Cake
(16, 5, 1, 0.30), -- Flour (kg)
(17, 5, 5, 0.25), -- Butter (kg)
(18, 5, 6, 0.33), -- Eggs (dozen)
(19, 5, 8, 15.00),-- Vanilla (ml)

-- Product 6: Dark Chocolate Truffle Cake
(20, 6, 1, 0.20), -- Flour (kg)
(21, 6, 4, 0.40), -- Cocoa (kg)
(22, 6, 14, 0.50),-- Heavy Cream (Liters)
(23, 6, 5, 0.20), -- Butter (kg)

-- Product 7: Nutella Stuffed Cookie (Mapped with Cocoa & Butter)
(24, 7, 1, 0.35), -- Flour (kg)
(25, 7, 5, 0.25), -- Butter (kg)
(26, 7, 4, 0.10), -- Cocoa (kg)
(27, 7, 2, 0.20), -- Caster Sugar (kg)

-- Product 8: Espresso Brownie Box (Mapped with Vanilla & Cocoa)
(28, 8, 1, 0.30), -- Flour (kg)
(29, 8, 4, 0.30), -- Cocoa (kg)
(30, 8, 5, 0.30), -- Butter (kg)
(31, 8, 8, 20.00),-- Vanilla (ml)

-- Product 9: White Choc Macadamia (Mapped with Walnuts & Sugar)
(32, 9, 1, 0.35), -- Flour (kg)
(33, 9, 5, 0.25), -- Butter (kg)
(34, 9, 2, 0.20), -- Caster Sugar (kg)
(35, 9, 12, 0.15),-- Walnuts (kg)

-- Product 10: Red Velvet Cream Cheese Cake
(36, 10, 1, 0.30),-- Flour (kg)
(37, 10, 4, 0.10),-- Cocoa (kg)
(38, 10, 15, 0.40),-- Cream Cheese (kg)
(39, 10, 6, 0.25),-- Eggs (dozen)

-- Product 11: Brookies Box
(40, 11, 1, 0.35),-- Flour (kg)
(41, 11, 4, 0.15),-- Cocoa (kg)
(42, 11, 5, 0.25),-- Butter (kg)
(43, 11, 7, 0.15),-- Dark Choc Chips (kg)

-- Product 12: Oatmeal Raisin Cookie (Mapped with Brown Sugar & Butter)
(44, 12, 1, 0.35),-- Flour (kg)
(45, 12, 3, 0.25),-- Brown Sugar (kg)
(46, 12, 5, 0.20),-- Butter (kg)
(47, 12, 6, 0.16),-- Eggs (dozen)

-- Product 13: Lemon Drizzle Loaf (Mapped with Caster Sugar & Butter)
(48, 13, 1, 0.30),-- Flour (kg)
(49, 13, 2, 0.25),-- Caster Sugar (kg)
(50, 13, 5, 0.25),-- Butter (kg)
(51, 13, 6, 0.33),-- Eggs (dozen)

-- Product 14: Peanut Butter Swirl Brownie (Mapped with Brown Sugar & Cocoa)
(52, 14, 1, 0.30),-- Flour (kg)
(53, 14, 4, 0.25),-- Cocoa (kg)
(54, 14, 5, 0.25),-- Butter (kg)
(55, 14, 3, 0.20),-- Brown Sugar (kg)

-- Product 15: Funfetti Birthday Cookie (Mapped with Vanilla & Sugar)
(56, 15, 1, 0.40),-- Flour (kg)
(57, 15, 5, 0.25),-- Butter (kg)
(58, 15, 2, 0.25),-- Caster Sugar (kg)
(59, 15, 8, 15.00);-- Vanilla (ml)




--MOD 3--


insert into customers values
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


insert into customer_addresses values
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


insert into orders values
(101, 1, '2026-03-20', 1200.00, 60.00, 0.00, 1260.00),
(102, 2, '2026-03-20', 2500.00, 125.00, 0.00, 2625.00),
(103, 3, '2026-03-20', 1350.00, 67.50, 0.00, 1417.50),
(104, 4, '2026-03-21', 500.00, 25.00, 0.00, 525.00),
(105, 5, '2026-03-21', 1500.00, 75.00, 100.00, 1475.00), -- Applied a 100rs discount here
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
(116, 16, '2026-03-24', 2800.00, 140.00, 200.00, 2740.00), -- 200rs discount
(117, 1, '2026-03-24', 1400.00, 70.00, 0.00, 1470.00),  -- Hamza's second order
(118, 17, '2026-03-25', 240.00, 12.00, 0.00, 252.00),
(119, 18, '2026-03-25', 1500.00, 75.00, 0.00, 1575.00),
(120, 19, '2026-03-25', 500.00, 25.00, 0.00, 525.00),
(121, 2, '2026-03-25', 1350.00, 67.50, 0.00, 1417.50),  -- Sara's second order
(122, 20, '2026-03-25', 280.00, 14.00, 0.00, 294.00),
(123, 3, '2026-03-26', 1400.00, 70.00, 0.00, 1470.00),  -- Bilal's second order
(124, 4, '2026-03-26', 1200.00, 60.00, 0.00, 1260.00),
(125, 5, '2026-03-26', 2500.00, 125.00, 0.00, 2625.00),
(126, 6, '2026-03-26', 300.00, 15.00, 0.00, 315.00),
(127, 7, '2026-03-26', 1300.00, 65.00, 0.00, 1365.00),
(128, 8, '2026-03-26', 1350.00, 67.50, 0.00, 1417.50),
(129, 9, '2026-03-26', 560.00, 28.00, 0.00, 588.00),
(130, 10, '2026-03-26', 2800.00, 140.00, 0.00, 2940.00);


insert into order_details values
(1, 101, 1, 1, 1200.00, 1200.00), -- 1 Walnut Brownie Box
(2, 102, 6, 1, 2500.00, 2500.00), -- 1 Truffle Cake
(3, 103, 2, 1, 1350.00, 1350.00), -- 1 Salted Caramel Brownie
(4, 104, 3, 2, 250.00, 500.00),   -- 2 Double Choc Cookies
(5, 105, 5, 1, 1500.00, 1500.00), -- 1 Vanilla Pound Cake
(6, 106, 10, 1, 2800.00, 2800.00),-- 1 Red Velvet Cake
(7, 107, 1, 1, 1200.00, 1200.00), 
(8, 108, 4, 2, 280.00, 560.00),   -- 2 Pecan Cookies
(9, 109, 11, 1, 1400.00, 1400.00),-- 1 Brookies Box
(10, 110, 7, 1, 300.00, 300.00),  -- 1 Nutella Cookie
(11, 111, 6, 1, 2500.00, 2500.00),
(12, 112, 8, 1, 1300.00, 1300.00),-- 1 Espresso Brownie Box
(13, 113, 14, 1, 1350.00, 1350.00),
(14, 114, 12, 2, 220.00, 440.00), -- 2 Oatmeal Raisin Cookies
(15, 115, 1, 1, 1200.00, 1200.00),
(16, 116, 10, 1, 2800.00, 2800.00),
(17, 117, 13, 1, 1400.00, 1400.00),
(18, 118, 15, 1, 240.00, 240.00), -- 1 Funfetti Cookie
(19, 119, 5, 1, 1500.00, 1500.00),
(20, 120, 3, 2, 250.00, 500.00),
(21, 121, 2, 1, 1350.00, 1350.00),
(22, 122, 9, 1, 280.00, 280.00),  -- 1 Macadamia Cookie
(23, 123, 11, 1, 1400.00, 1400.00),
(24, 124, 1, 1, 1200.00, 1200.00),
(25, 125, 6, 1, 2500.00, 2500.00),
(26, 126, 7, 1, 300.00, 300.00),
(27, 127, 8, 1, 1300.00, 1300.00),
(28, 128, 14, 1, 1350.00, 1350.00),
(29, 129, 4, 2, 280.00, 560.00),
(30, 130, 10, 1, 2800.00, 2800.00);


insert into payments values
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



--MOD 4--


insert into delivery_riders values
(1, 'Kamran', 'Baqir', '0300-1110001', 'Honda CD 70'),
(2, 'Shoaib', 'Tariq', '0300-1110002', 'Suzuki GS 150'),
(3, 'Babar', 'Ali', '0300-1110003', 'Honda CG 125'),
(4, 'Shaheen', 'Shah', '0300-1110004', 'Yamaha YBR 125'),
(5, 'Fakhar', 'Zaman', '0300-1110005', 'Honda Pridor');


insert into deliveries values
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
(17, 117, 2, 1, '2026-03-24 17:10:00', '2026-03-24 17:45:00', 1), -- Hamza's 2nd Order

(18, 118, 3, 17, '2026-03-25 09:05:00', '2026-03-25 09:40:00', 1),
(19, 119, 4, 18, '2026-03-25 11:50:00', '2026-03-25 12:30:00', 1),
(20, 120, 5, 19, '2026-03-25 13:40:00', '2026-03-25 14:20:00', 1),
(21, 121, 1, 2, '2026-03-25 16:15:00', '2026-03-25 16:55:00', 1), -- Sara's 2nd Order
(22, 122, 2, 20, '2026-03-25 18:30:00', '2026-03-25 19:10:00', 1),

(23, 123, 3, 3, '2026-03-26 10:00:00', '2026-03-26 10:45:00', 1), -- Bilal's 2nd Order
(24, 124, 4, 4, '2026-03-26 11:20:00', '2026-03-26 12:00:00', 1),
(25, 125, 5, 5, '2026-03-26 13:10:00', '2026-03-26 13:50:00', 1),
(26, 126, 1, 6, '2026-03-26 14:45:00', '2026-03-26 15:20:00', 1),
(27, 127, 2, 7, '2026-03-26 16:00:00', '2026-03-26 16:40:00', 1),
(28, 128, 3, 8, '2026-03-26 17:30:00', null, 0), -- Currently out for delivery
(29, 129, 4, 9, '2026-03-26 18:15:00', null, 0), -- Currently out for delivery
(30, 130, 5, 10, '2026-03-26 18:45:00', null, 0); -- Currently out for delivery



--MOD 5--

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

