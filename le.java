import java.util.List;
import java.util.Arrays;
import java.util.ArrayList;

class Solution {
    public int[][] merge(int[][] intervals) {
        //保存结果的数组
        List<int[] > result=new ArrayList<>();
        //对数组进行排序
        Arrays.sort(intervals, (a, b) -> a[0] - b[0]);
        int currentStart = intervals[0][0];
        int currentEnd = intervals[0][1];
        for(int i = 1; i < intervals.length; i++){
            //如果当前区间的开始小于等于上一个区间的结束，则合并
            if(intervals[i][0] <= currentEnd){
                currentEnd=Math.max(currentEnd,intervals[i][1]);
                result.add(new int[]{currentStart,currentEnd});
            }else{
                //如果当前区间的开始大于上一个区间的结束，则不合并
                result.add(new int[]{currentStart,currentEnd});
                currentStart=intervals[i][0];
                currentEnd=intervals[i][1];
            }
        }
        result.add(new int[]{currentStart,currentEnd});
        return result.toArray(new int[result.size()][]);
    }
}