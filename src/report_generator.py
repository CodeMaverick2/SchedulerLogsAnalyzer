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
            total_logs = len(self.df)
            completed_logs = len(self.df[self.df['Status'] == 'schedulerLogCompleted'])
            skipped_logs = total_logs - completed_logs
            
            # Analyze completed logs
            completed_df = self.df[self.df['Status'] == 'schedulerLogCompleted']
            if len(completed_df) == 0:
                logging.warning("No completed logs found")
                
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
            scheduled_percent = (total_scheduled / total_tasks * 100) if total_tasks > 0 else 0
            
            # Get skipped log examples with safety checks
            skipped_df = self.df[self.df['Status'] != 'schedulerLogCompleted']
            if len(skipped_df) >= 2:
                skipped_examples = skipped_df[['Id', 'Start Time']].head(2)
            else:
                skipped_examples = pd.DataFrame({'Id': ['N/A', 'N/A'], 'Start Time': ['N/A', 'N/A']})
                
            # Additional Analysis
            # 1. Peak Time Analysis
            completed_df['Hour'] = pd.to_datetime(completed_df['Start Time']).dt.hour
            peak_hour = completed_df['Hour'].mode().iloc[0]
            tasks_in_peak_hour = len(completed_df[completed_df['Hour'] == peak_hour])
            
            # 2. Efficiency Metrics
            avg_tasks_per_batch = batch_runs['Total Tasks'].mean() if batch_count > 0 else 0
            efficiency_ratio = (total_tasks / completed_logs) if completed_logs > 0 else 0
            
            # 3. Duration Distribution
            duration_stats = completed_df['Duration'].describe()
            
            # 4. Success Rate Trends
            hourly_success_rate = (completed_df.groupby('Hour').size() / 
                                 self.df.groupby(pd.to_datetime(self.df['Start Time']).dt.hour).size() * 100)
            best_performance_hour = hourly_success_rate.idxmax()
            
            # Enhanced Task Analysis
            scheduled_df = completed_df[completed_df['# Scheduled Tasks'] > 0]
            unscheduled_df = completed_df[completed_df['# Unscheduled Tasks'] > 0]
            
            # Scheduled Tasks Analysis
            scheduled_metrics = {
                'total': total_scheduled,
                'avg_per_batch': scheduled_df['# Scheduled Tasks'].mean() if len(scheduled_df) > 0 else 0,
                'max_in_batch': scheduled_df['# Scheduled Tasks'].max() if len(scheduled_df) > 0 else 0,
                'batches_with_scheduled': len(scheduled_df),
                'avg_duration': scheduled_df['Duration'].mean() if len(scheduled_df) > 0 else 0
            }
            
            # Unscheduled Tasks Analysis
            unscheduled_metrics = {
                'total': total_unscheduled,
                'avg_per_batch': unscheduled_df['# Unscheduled Tasks'].mean() if len(unscheduled_df) > 0 else 0,
                'max_in_batch': unscheduled_df['# Unscheduled Tasks'].max() if len(unscheduled_df) > 0 else 0,
                'batches_with_unscheduled': len(unscheduled_df),
                'avg_duration': unscheduled_df['Duration'].mean() if len(unscheduled_df) > 0 else 0
            }

            report = f"""Scheduler Log Analysis Report
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Log Distribution Details
Total Logs: {total_logs}
Completed Logs: {completed_logs}
Skipped Logs: {skipped_logs}
Success Rate: {(completed_logs/total_logs*100):.1f}%

Task Distribution Details
Total Tasks Processed: {total_tasks}

Scheduled Tasks Analysis
Total Scheduled Tasks: {scheduled_metrics['total']}
Average Scheduled Tasks per Batch: {scheduled_metrics['avg_per_batch']:.1f}
Maximum Scheduled Tasks in a Batch: {scheduled_metrics['max_in_batch']}
Number of Batches with Scheduled Tasks: {scheduled_metrics['batches_with_scheduled']}
Average Duration for Scheduled Batches: {scheduled_metrics['avg_duration']:.2f} minutes

Unscheduled Tasks Analysis
Total Unscheduled Tasks: {unscheduled_metrics['total']}
Average Unscheduled Tasks per Batch: {unscheduled_metrics['avg_per_batch']:.1f}
Maximum Unscheduled Tasks in a Batch: {unscheduled_metrics['max_in_batch']}
Number of Batches with Unscheduled Tasks: {unscheduled_metrics['batches_with_unscheduled']}
Average Duration for Unscheduled Batches: {unscheduled_metrics['avg_duration']:.2f} minutes

Batch Processing Summary
Total Batch Runs: {batch_count}
Average Batch Duration: {avg_batch_duration:.2f} minutes
Maximum Batch Size: {max_batch['Total Tasks']} tasks (ID: {max_batch['Id']})
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