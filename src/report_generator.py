import pandas as pd
from datetime import datetime
from typing import Dict
import logging

class ReportGenerator:
    def __init__(self):
        self.df = None
        
    def generate_report(self, csv_path: str) -> dict:
        try:
            # Read CSV
            self.df = pd.read_csv(csv_path)
            if len(self.df) == 0:
                logging.error("Empty CSV file")
                return None
                
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Calculate basic metrics
            total_runs = len(self.df)
            completed_runs = len(self.df[self.df['Status'] == 'schedulerLogCompleted'])
            skipped_runs = total_runs - completed_runs
            
            # Filter for data with duration > 0
            df_filtered = self.df[(self.df['Duration'] > 0)]
            # Analyze completed runs
            completed_df = self.df[self.df['Status'] == 'schedulerLogCompleted']
            if len(completed_df) == 0:
                logging.warning("No completed runs found")
                
            batch_runs = completed_df[completed_df['Total Tasks'] > 1]
            individual_runs = completed_df[completed_df['Total Tasks'] == 1]
            
            # Calculate batch run statistics with safety checks
            batch_count = len(batch_runs)
            if batch_count > 0:
                avg_batch_duration = batch_runs['Duration'].mean()
                min_batch = batch_runs.loc[batch_runs['Duration'].idxmin()]
                max_batch = batch_runs.loc[batch_runs['Duration'].idxmax()]
            else:
                logging.warning("No batch runs found")
                avg_batch_duration = 0
                min_batch = {'Duration': 0, 'Id': 'N/A', 'Total Tasks': 0}
                max_batch = {'Duration': 0, 'Id': 'N/A', 'Total Tasks': 0}
            
            # Calculate task proportions with safety checks
            total_scheduled = completed_df['# Scheduled Tasks'].sum()
            total_unscheduled = completed_df['# Unscheduled Tasks'].sum()
            total_tasks = total_scheduled + total_unscheduled
            
            # Get skipped run details
            skipped_df = self.df[self.df['Status'] != 'schedulerLogCompleted']
            skipped_ids = skipped_df['Id'].tolist()[:5] if len(skipped_df) > 0 else ['N/A']
            
            # Get failed run details if available
            failed_df = self.df[self.df['Status'] == 'schedulerLogFailed'] if 'schedulerLogFailed' in self.df['Status'].unique() else pd.DataFrame()
            failed_ids = failed_df['Id'].tolist()[:5] if len(failed_df) > 0 else ['N/A']
            
            # Enhanced Task Analysis
            # Filter for rows with Duration > 0
            scheduled_df = df_filtered[df_filtered['# Scheduled Tasks'] > 0]
            unscheduled_df = df_filtered[df_filtered['# Unscheduled Tasks'] > 0]
            
            # Scheduled Tasks Analysis
            scheduled_metrics = {
                'total': total_scheduled,
                'avg_per_batch': scheduled_df['# Scheduled Tasks'].mean() if len(scheduled_df) > 0 else 0,
                'batches_with_scheduled': len(scheduled_df),
                'avg_duration': scheduled_df['Duration'].mean() if len(scheduled_df) > 0 else 0
            }
            
            # Unscheduled Tasks Analysis
            unscheduled_metrics = {
                'total': total_unscheduled,
                'avg_per_batch': unscheduled_df['# Unscheduled Tasks'].mean() if len(unscheduled_df) > 0 else 0,
                'batches_with_unscheduled': len(unscheduled_df),
                'avg_duration': unscheduled_df['Duration'].mean() if len(unscheduled_df) > 0 else 0
            }
            
            # Daily Insights
            insights = []
            
            # Insight 1: Task ratio (scheduled vs unscheduled)
            if total_tasks > 0:
                scheduled_percent = (total_scheduled / total_tasks) * 100
                unscheduled_percent = (total_unscheduled / total_tasks) * 100
                insights.append(f"Scheduled vs Unscheduled Ratio: {scheduled_percent:.1f}% / {unscheduled_percent:.1f}%")
            
            # Insight 3: Completion Rate
            completion_rate = (completed_runs / total_runs * 100) if total_runs > 0 else 0
            insights.append(f"Run Completion Rate: {completion_rate:.1f}%")
            
            # Insight 4: Average Tasks Per Run
            avg_tasks_per_run = total_tasks / completed_runs if completed_runs > 0 else 0
            insights.append(f"Average Tasks Per Run: {avg_tasks_per_run:.1f}")
            
            # Insight 5: Duration metrics
            insights.append(f"Average Run Duration: {avg_batch_duration:.2f} minutes")
            
            # Insight 7: Run efficiency 
            if completed_runs > 0:
                avg_scheduled_per_run = total_scheduled / completed_runs
                avg_unscheduled_per_run = total_unscheduled / completed_runs
                insights.append(f"Avg Scheduled Tasks Per Run: {avg_scheduled_per_run:.1f}")
                insights.append(f"Avg Unscheduled Tasks Per Run: {avg_unscheduled_per_run:.1f}")

            # Check if skipped IDs and failed IDs are the same
            same_ids = set(skipped_ids) == set(failed_ids)
            
            # Format the Batch Processing Summary section based on whether IDs are the same
            if same_ids:
                batch_summary = f"""Batch Processing Summary
Total Batch Runs: {batch_count}
Average Batch Duration: {avg_batch_duration:.2f} minutes
Maximum Batch Size: {max_batch['Total Tasks']} tasks (ID: {max_batch['Id']})
Maximum Duration: {max_batch['Duration']:.2f} minutes (ID: {max_batch['Id']})
Minimum Duration: {min_batch['Duration']:.2f} minutes (ID: {min_batch['Id']})
Problem IDs: {', '.join(skipped_ids[:5])}"""
            else:
                batch_summary = f"""Batch Processing Summary
Total Batch Runs: {batch_count}
Average Batch Duration: {avg_batch_duration:.2f} minutes
Maximum Batch Size: {max_batch['Total Tasks']} tasks (ID: {max_batch['Id']})
Maximum Duration: {max_batch['Duration']:.2f} minutes (ID: {max_batch['Id']})
Minimum Duration: {min_batch['Duration']:.2f} minutes (ID: {min_batch['Id']})
Skipped IDs: {', '.join(skipped_ids[:5])}
Failed IDs: {', '.join(failed_ids[:5])}"""

            report = f"""Scheduler Run Analysis Report
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Run Distribution Details
Total Runs: {total_runs}
Completed Runs: {completed_runs}
Skipped Runs: {skipped_runs}

Daily Insights
{insights[0]}
{insights[1]}
{insights[2]}
{insights[3]}
{insights[4]}
{insights[5]}

{batch_summary}
"""

            return {"content": report}
            
        except pd.errors.EmptyDataError:
            logging.error("Empty CSV file or no data found")
            return None
        except pd.errors.ParserError:
            logging.error("Error parsing CSV file")
            return None
        except KeyError as e:
            logging.error(f"Missing required column: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"Report generation failed: {str(e)}")
            return None 