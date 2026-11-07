-- Most common permit types
SELECT pt.permit_type, COUNT(*) AS permits
FROM fact_permit f
JOIN dim_permit_type pt ON f.permit_type_key = pt.permit_type_key
GROUP BY pt.permit_type
ORDER BY permits DESC;

-- The odd community area
SELECT community_area_key, COUNT(*) AS permits
FROM fact_permit
WHERE community_area_key NOT BETWEEN 1 AND 77
GROUP BY community_area_key;

SELECT ca.community_area_name, COUNT(*) AS permits
FROM fact_permit f
JOIN dim_community_area ca ON f.community_area_key = ca.community_area_key
GROUP BY ca.community_area_name
ORDER BY permits DESC
LIMIT 10;