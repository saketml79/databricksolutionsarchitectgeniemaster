-- Reuse discovery: expected asset_customer_gold.
SELECT * FROM databricks_architect_agent.agent_demo.find_reusable_assets('customer');

-- Lineage impact: expected Customer 360 Executive Dashboard and customer-profile-api.
SELECT * FROM databricks_architect_agent.agent_demo.downstream_impact('asset_customer_gold');

-- Cost drivers: expected high-cost warehouse and idle legacy cluster signals.
SELECT * FROM databricks_architect_agent.agent_demo.summarize_cost_drivers('customer');

-- Policy constraints: expected PII isolation.
SELECT policy_id, requirement_text, enforcement_boundary
FROM databricks_architect_agent.agent_demo.platform_policy
WHERE applies_to_domain IN ('customer', 'acquisition') AND status = 'ACTIVE';

-- Retail POS certified metric benchmark: expected daily store-level net sales and gross profit.
SELECT sales_date, region, sum(net_sales_usd) AS net_sales_usd, sum(gross_profit_usd) AS gross_profit_usd
FROM databricks_architect_agent.retail_pos.v_daily_store_sales
GROUP BY sales_date, region
ORDER BY sales_date, region;

-- Retail POS semantic join benchmark: expected category, region, and segment results without direct customer PII.
SELECT store.region, product.category, segment.segment_name, sum(sale.net_sales_usd) AS net_sales_usd
FROM databricks_architect_agent.retail_pos.fact_pos_sale sale
JOIN databricks_architect_agent.retail_pos.dim_store store ON sale.store_id = store.store_id
JOIN databricks_architect_agent.retail_pos.dim_product product ON sale.product_id = product.product_id
LEFT JOIN databricks_architect_agent.retail_pos.dim_customer_segment segment ON sale.customer_segment_id = segment.customer_segment_id
GROUP BY store.region, product.category, segment.segment_name
ORDER BY net_sales_usd DESC;