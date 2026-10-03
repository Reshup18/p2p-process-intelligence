

--2. Drop the existing table if re-running
DROP TABLE IF EXISTS p2p_event_logs;

--3. Define schema with strict data types
CREATE TABLE p2p_event_logs(
    event_id BIGSERIAL PRIMARY KEY,
	case_id VARCHAR(100) NOT NULL,
	activity_name VARCHAR(255) NOT NULL,
	event_timestamp TIMESTAMP NOT NULL,
	resource_id VARCHAR(100) 
);

--4. Create a B-tree composite index optimized for window functions
CREATE INDEX idx_case_timestamp ON p2p_event_logs(case_id, event_timestamp ASC);


COPY p2p_event_logs(event_id,case_id, activity_name, event_timestamp, resource_id)
FROM 'C:/Users/reshu/p2p_process_intelligence/bpi_2019_raw.csv'
WITH (
    FORMAT csv,
	HEADER true,
	DELIMITER ','
);


SELECT 
    COUNT(*) AS total_rows,
	COUNT(DISTINCT case_id) AS total_cases,
	MIN(event_timestamp) AS earliest_event,
	MAX(event_timestamp) AS latest_event
FROM p2p_event_logs;	


-- Filter out corrupt legacy dates before 2018
DELETE FROM p2p_event_logs 
WHERE event_timestamp < '2018-01-01 00:00:00'
    OR event_timestamp > '2019-06-30 23:59:59';



--Query 1: Calculate handoff durations between consecutive activities
WITH SequencedEvent AS (
    SELECT 
	    case_id,
		activity_name AS source_node,
		event_timestamp AS t1,
		LEAD(activity_name) OVER(PARTITION BY case_id ORDER BY event_timestamp ASC) AS target_node,
		LEAD(event_timestamp) OVER(PARTITION BY case_id ORDER BY event_timestamp ASC) As t2
	FROM p2p_event_logs
	WHERE event_timestamp >= '2018-01-01 00:00:00' --clean corrupt 1948 timestamp
),
Transitions AS (
    SELECT 
	    source_node,
		target_node,
		EXTRACT(EPOCH FROM (t2 - t1))/3600.0 AS delay_hours
	FROM SequencedEvent
	WHERE target_node IS NOT NULL  --Exclude end of the process cases
)
SELECT
    source_node,
	target_node,
	COUNT(*) AS transition_volume,
	ROUND(AVG(delay_hours)::numeric,2) AS avg_delay_hours,
	ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY delay_hours)::numeric, 2) AS median_delay_hours
FROM Transitions
GROUP BY source_node, target_node
ORDER BY transition_volume DESC
LIMIT 15;


-- Query 2: Case Variant Path Aggregation
WITH CaseTraces AS (
    SELECT
	    case_id,
		STRING_AGG(activity_name, '->' ORDER BY event_timestamp ASC) AS full_variant_path,
		MIN(event_timestamp) AS start_time,
		MAX(event_timestamp) AS end_time,
		EXTRACT(EPOCH FROM (MAX(event_timestamp) - MIN(event_timestamp)))/ 86400.0 AS total_duration_days
	FROM p2p_event_logs
	WHERE event_timestamp >='2018-01-01 00:00:00'
	GROUP BY case_id
)
SELECT
    full_variant_path,
	COUNT(*) AS case_count,
	ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER()),2) AS varient_percentage,
	ROUND(AVG(total_duration_days)::numeric,2) AS avg_duration_days,
	ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_duration_days)::numeric, 2) AS median_duration_days
FROM caseTraces	
GROUP BY full_variant_path
ORDER BY case_count DESC
LIMIT 10;
